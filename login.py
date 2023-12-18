import pickle
from json import load
from os import listdir
import sys
from time import time
import logging
import requests
import ddddocr
import re

logging.basicConfig(level=logging.INFO,filename='info.log',format="%(asctime)s %(filename)s %(funcName)s：line %(lineno)d %(levelname)s %(message)s")



class Login:
    def __init__(self, hostname, username, password, questionid='0', answer=None, cookies_flag=True):
        self.session = requests.session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'})
        self.hostname = hostname
        self.username = str(username)
        self.password = str(password)

        self.questionid = questionid
        self.answer = answer
        self.cookies_flag = cookies_flag
        self.ocr = ddddocr.DdddOcr()


    def form_hash(self):
        rst = self.session.get(f'https://{self.hostname}/member.php?mod=logging&action=login').text
        logininfo = re.search(r'<div id="main_messaqge_(.+?)">', rst)
        if logininfo is not None:
            loginhash = re.search(r'<div id="main_messaqge_(.+?)">', rst).group(1)
        else:
            loginhash = ""
        formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', rst).group(1)
        logging.info(f'loginhash : {loginhash} , formhash : {formhash} ')
        return loginhash, formhash

    def verify_code_once(self):
        rst = self.session.get(f'https://{self.hostname}/misc.php?mod=seccode&action=update&idhash=cSA&0.3701502461393815&modid=member::logging').text
        update = re.search(r'update=(.+?)&idhash=', rst).group(1)

        code_headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'hostname': f'{self.hostname}',
            'Referer': f'https://{self.hostname}/member.php?mod=logging&action=login',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
        }
        rst = self.session.get(f'https://{self.hostname}/misc.php?mod=seccode&update={update}&idhash=cSA',
                            headers=code_headers)

        return self.ocr.classification(rst.content)


    def verify_code(self,num = 10):
        while num>0:
            num -=1
            code = self.verify_code_once()
            verify_url = f'https://{self.hostname}/misc.php?mod=seccode&action=check&inajax=1&modid=member::logging&idhash=cSA&secverify={code}'
            res = self.session.get(verify_url).text

            if 'succeed' in res:
                logging.info('验证码识别成功，验证码:'+code)
                return code
            else:
                logging.info('验证码识别失败，重新识别中...')

        logging.error('验证码获取失败，请增加验证次数或检查当前验证码识别功能是否正常')
        return ''

    def account_login_without_verify(self):

        loginhash, formhash = self.form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1'
        formData = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'username': self.username,
            'password': self.password,
            'handlekey':'ls',
        }
        login_rst = self.session.post(login_url, data=formData).text
        if 'succeed' in login_rst:
            logging.info('登陆成功')
            return True
        else:
            logging.info('登陆失败，请检查账号或密码是否正确')
            return False



    def account_login(self):
        try:
            if self.account_login_without_verify():
                return True
        except Exception:
            logging.error('存在验证码，登陆失败，准备获取验证码中', exc_info=True)

        code = self.verify_code()
        if code =='':
            return False

        loginhash, formhash = self.form_hash()
        login_url = f'https://{self.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}&inajax=1'
        formData = {
            'formhash': formhash,
            'referer': f'https://{self.hostname}/',
            'loginfield': self.username,
            'username': self.username,
            'password': self.password,
            'questionid': self.questionid,
            'answer': self.answer,
            'cookietime': 2592000,
            'seccodehash': 'cSA',
            'seccodemodid': 'member::logging',
            'seccodeverify': code,  # verify code
        }
        login_rst = self.session.post(login_url, data=formData).text
        if 'succeed' in login_rst:
            logging.info('登陆成功')
            return True
        else:
            logging.info('登陆失败，请检查账号或密码是否正确')
            return False


    def cookies_login(self):
        cookies_name = 'COOKIES-' + self.username
        if cookies_name in listdir():
            try:
                with open(cookies_name, 'rb') as f:
                    self.session = pickle.load(f)
                response = self.session.get(f'https://{self.hostname}/home.php?mod=space').text
                
                if "退出" in response and "登录" not in response:
                    logging.info('从文件中恢复Cookie成功，跳过登录。')
                    return True
            except Exception:
                logging.warning('Cookie失效，使用账号密码登录。')
        else:
            logging.info('初次登录未发现Cookie，使用账号密码登录。')
        return False

   
    def go_home(self):
        return self.session.get(f'https://{self.hostname}/forum.php').text

    def get_conis(self):
        try:
            res = self.session.get(f'https://{self.hostname}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu').text
            coins = re.search(r'<span id="hcredit_2">(.+?)</span>', res).group(1)
            logging.info(f'当前金币数量：{coins}')
        except Exception:
            logging.error('获取金币数量失败！', exc_info=True)

    def main(self):

        try:
            if self.cookies_flag and self.cookies_login():
                logging.info('成功使用cookies登录')
            else:
                self.account_login()
            res = self.go_home()
            self.post_formhash = re.search(r'<input type="hidden" name="formhash" value="(.+?)" />', res).group(1)
            credit =re.search(r' class="showmenu">(.+?)</a>', res).group(1)
            logging.info(f'{credit},提交文章formhash:{self.post_formhash}')

            self.get_conis()

            cookies_name = 'COOKIES-' + self.username
            with open(cookies_name, 'wb') as f:
                pickle.dump(self.session, f)
                logging.info('新的Cookie已保存。')

        except Exception:
            logging.error('失败，发生了一个错误！', exc_info=True)
            sys.exit()


if __name__ == '__main__':
    login = Login('','','')
    login.main()
