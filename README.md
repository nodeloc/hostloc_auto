# hostloc_auto
loc机器人，全自动登录discuz论坛，签到，刷空间，回帖刷币

使用ChatGPT AI回帖。不容易被封号哦。

V2.0 增加了多用户的支持以及多ChatGPT key的轮询。

##
```json
{"role": "system", "content": "你是一个常年混迹hostloc的人，帮助回答一些问题."},
```
prompt请修改一下，以避免你和别人的答案类似，不同的prompt会产生截然不同的回答。

## 环境
centos + python3.9

## 运行方式
 - 克隆仓库
 - discuz.py文件内修改论坛地址、账号、密码等信息

 ```
    hostname = ''   #论坛地址
    username = ''   #账号
    password = ''   #密码
    chatgpt_key = '' #ChatGPT的key
```

```angular2html
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
```

 - 安装依赖，可以先直接运行 `python3 discuz.py`，缺哪个库装那个，直到日志（info.log）中显示登录成功的信息
 - crontab添加定时任务，每过6分钟执行一次回帖示例 `*/6 * * * * cd /root/discuz_bot/ && python3 discuz.py` 目录改成自己的

## 说明
 - 自动识别验证码登录
 - 先尝试无验证码登录一次，失败后尝试自动识别验证码登录
 - 针对Hostloc编写，如果是其它Discuz论坛修改一下基本也能用。
