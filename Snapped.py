import random
import login
import time
import logging
import re
from random import randint
from bs4 import BeautifulSoup
import requests
import sys
import config

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
        return self.session.get(f'https://{self.hostname}/forum.php?mod=guide&view=new').text

    def get_reply_tid_list(self):
        tids = []
        soup = BeautifulSoup(self.go_hot(), features="html.parser")
        replys = []
        reply = soup.select_one('#threadlist')
        replys.append(reply)
        pattern = re.compile(r'thread-')
        for reply in replys:
            for a in reply.find_all("a", href=pattern):
                if '机器人' in str(a) or '通知' in str(a) or '封号' in str(a):
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



    def generate_random_numbers(self, start, end, count):
        random_numbers = []
        for _ in range(count):
            random_number = random.randint(start, end)
            random_numbers.append(random_number)
        return random_numbers

    def signin(self):
        signin_url = f'https://{self.hostname}'
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
        reply_url = f'https://{self.hostname}/forum.php?mod=post&action=reply&tid={tid}&extra=&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1'
        data = {
            'file': '',
            'message': config.auto_replay_content,
            'posttime': int(time.time()),
            'formhash': self.formhash,
            'usesig': 1,
            'subject': '',
        }

        res = self.session.post(reply_url, data=data).text
        if 'succeed' in res:
            url = re.search(r'succeedhandle_fastpost\(\'(.+?)\',', res).group(1)
            logging.info(f'T楼发送成功，tid:{tid},链接:{"https://" + self.hostname + "/" + url}')
        else:
            logging.error('T楼发送失败\t' + res)


if __name__ == '__main__':
    looptimes = config.auto_replay_times
    # 循环执行每对用户名、密码和ChatGPT密钥的组合
    while looptimes>0:
        for credentials in config.user_credentials:
            hostname = 'hostloc.com'
            username = credentials['username']
            password = credentials['password']
            # 随机选择一个ChatGPT密钥
            chatgpt_key = random.choice(config.chatgpt_keys)
            discuz = Discuz(hostname, username, password, chatgpt_key)
            discuz.login()
            # 执行方法
            discuz.reply(config.auto_replay_tid)
        looptimes = looptimes-1
        time.sleep(config.auto_replay_interval)
