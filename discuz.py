import random
import login
import time
import logging
import re
from random import randint
from bs4 import BeautifulSoup
import requests
import sys

logging.basicConfig(level=logging.INFO, filename='info.log', format="%(asctime)s %(filename)s %(funcName)s：line %(lineno)d %(levelname)s %(message)s")


class Discuz:
    def __init__(self, hostname, username, password, chatgpt_key, questionid='0', answer=None, cookies_flag=True, pub_url=''):
        self.chatgpt_key = chatgpt_key
        self.hostname = hostname
        if pub_url != '':
            self.hostname = self.get_host(pub_url)

        self.discuz_login = login.Login(self.hostname, username, password, questionid, answer, cookies_flag)

    def login(self):
        self.discuz_login.main()
        self.session = self.discuz_login.session
        self.formhash = self.discuz_login.post_formhash

    def get_host(self, pub_url):
        res = requests.get(pub_url)
        res.encoding = "utf-8"
        url = re.search(r'a href="https://(.+?)/".+?>.+?入口</a>', res.text)
        if url != None:
            url = url.group(1)
            logging.info(f'获取到最新的论坛地址:https://{url}')
            return url
        else:
            logging.error(f'获取失败，请检查发布页是否可用{pub_url}')
            return self.hostname

    def go_home(self):
        return self.session.get(f'https://{self.hostname}/forum.php').text

    def go_hot(self):
        return self.session.get(f'https://{self.hostname}/forum-45-1.html').text

    def get_reply_tid_list(self):
        tids = []
        soup = BeautifulSoup(self.go_hot(), features="html.parser")
        replys = []
        reply = soup.select_one('#threadlisttableid')
        replys.append(reply)
        pattern = re.compile(r'thread-')
        for reply in replys:
            for a in reply.find_all("a", href=pattern):
                if '机器人' in str(a) or '测试' in str(a) or '封号' in str(a):
                    continue
                url = a['href']
                match = re.search(r'thread-(\d+)', url)
                if match:
                    tids.append(match.group(1))
        return tids

    def get_reply_tid(self):
        tids = self.get_reply_tid_list()
        if len(tids) > 0:
            return tids[randint(0, len(tids) - 1)]
        else:
            logging.error('tid获取失败，退出')
            sys.exit()

    def chat_with_gpt(self, prompt):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.chatgpt_key,
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一个常年混迹hostloc的人，帮助回答一些问题."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        print("chatgpt response -->" + str(response_json))
        if "choices" in response_json:
            choices = response_json["choices"]
            if len(choices) > 0 and "message" in choices[0] and "content" in choices[0]["message"]:
                return choices[0]["message"]["content"]

        return None

    def generate_random_numbers(self, start, end, count):
        random_numbers = []
        for _ in range(count):
            random_number = random.randint(start, end)
            random_numbers.append(random_number)
        return random_numbers

    def signin(self):
        signin_url =  f'https://{self.hostname}'
        self.session.get(signin_url)

    def visit_home(self):
        start = 1  # 起始数字
        end = 50000  # 结束数字
        count = 10  # 随机数字的数量

        random_numbers = self.generate_random_numbers(start, end, count)
        for number in random_numbers:
            time.sleep(5)
            signin_url = f'https://{self.hostname}/space-uid-{number}.html'
            self.session.get(signin_url)

    def reply(self, tid, message=''):
        topic_url = f'https://{self.hostname}/thread-{tid}-1-1.html'
        res = self.session.get(topic_url).text
        prompt = "你好，请直接回复两句古诗"
        pattern = r'<meta\s+name="description"\s+content="([^"]+)"\s*/>'
        match = re.search(pattern, res)
        if match:
            prompt = match.group(1)

        response = self.chat_with_gpt(prompt)
        if response:
            reply_url = f'https://{self.hostname}/forum.php?mod=post&action=reply&tid={tid}&extra=&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1'
            data = {
                'file': '',
                'message': response,
                'posttime': int(time.time()),
                'formhash': self.formhash,
                'usesig': 1,
                'subject': '',
            }

            res = self.session.post(reply_url, data=data).text
            if 'succeed' in res:
                url = re.search(r'succeedhandle_fastpost\(\'(.+?)\',', res).group(1)
                logging.info(f'回复发送成功，tid:{tid}，回复:{response},链接:{"https://" + self.hostname + "/" + url}')
            else:
                logging.error('回复发送失败\t' + res)
        else:
            logging.error('ChatGPT未能成功获取回复\t')


if __name__ == '__main__':
    # 定义多个用户名、密码和ChatGPT密钥的组合
    user_credentials = [
        {'username': 'username1', 'password': 'password1'},
        {'username': 'username2', 'password': 'password2'},
        # 添加更多的用户名和密码组合
    ]

    chatgpt_keys = [
        'chatgpt_key1',
        'chatgpt_key2',
        # 添加更多的ChatGPT密钥
    ]

    # 循环执行每对用户名、密码和ChatGPT密钥的组合
    for credentials in user_credentials:
        hostname = 'hostloc.com'
        username = credentials['username']
        password = credentials['password']
        # 随机选择一个ChatGPT密钥
        chatgpt_key = random.choice(chatgpt_keys)
        discuz = Discuz(hostname, username, password, chatgpt_key)
        discuz.login()
        discuz.signin()
        discuz.visit_home()
        # 循环执行50次
        for i in range(50):
            # 执行方法
            discuz.reply(discuz.get_reply_tid())
            # 等待5分钟
            time.sleep(300)  # 5分钟 = 5 * 60秒 = 300秒