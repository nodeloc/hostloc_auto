from pyexpat.errors import messages

import login

from time import time
import logging
import re
from urllib.parse import quote
from random import randint
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlsplit, parse_qsl
import requests
import sys

logging.basicConfig(level=logging.INFO, filename='info.log', format="%(asctime)s %(filename)s %(funcName)s：line %(lineno)d %(levelname)s %(message)s")


class Discuz:
    def __init__(self, hostname, username, password, questionid='0', answer=None, cookies_flag=True, pub_url=''):
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
        return self.session.get(f'https://{self.hostname}/misc.php?mod=ranklist').text

    def get_reply_tid_list(self):
        tids = []
        soup = BeautifulSoup(self.go_hot(), features="html.parser")
        replys = []
        reply = soup.select_one('.bm_c')
        replys.append(reply)

        for reply in replys:
            for a in reply.find_all("a"):
                if '机器人' in str(a) or '测试' in str(a) or '封号' in str(a):
                    continue
                dt = dict(parse_qsl(urlsplit(a['href']).query))
                if 'tid' in dt.keys():
                    tids.append(dt['tid'])
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
            "Authorization": self.chatgpt_key
        }
        data = {
            "prompt": prompt,
            "max_tokens": 50,
            "temperature": 0.7
        }

        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        if "choices" in response_json:
            choices = response_json["choices"]
            if len(choices) > 0 and "text" in choices[0]:
                return choices[0]["text"]

        return None

    def reply(self, tid, message=''):

        # 提供一个初始的对话提示
        prompt = "你好，我是聊天机器人。"

        while True:
            user_input = input("用户：")
            prompt += "\n用户：" + user_input

            response = self.chat_with_gpt(prompt)
            if response:
                reply_url = f'https://{self.hostname}/forum.php?mod=post&action=reply&tid={tid}&extra=&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1'
                data = {
                    'file': '',
                    'message': response,
                    'posttime': int(time()),
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
    hostname = 'hostloc.com'
    username = ''
    password = ''
    chatgpt_key = ''
    discuz = Discuz(hostname, username, password)
    discuz.login()
    discuz.reply(discuz.get_reply_tid())

