# hostloc_auto
loc机器人，全自动登录discuz论坛，签到，刷空间，回帖刷币


## 环境
centos + python3.9

## 运行方式
 - 克隆仓库
 - discuz.py文件内修改论坛地址、账号、密码等信息

 ```
    hostname = ''   #论坛地址
    username = ''   #账号
    password = ''   #密码
```

 - 安装依赖，可以先直接运行 `python3 discuz.py`，缺哪个库装那个，直到日志（info.log）中显示登录成功的信息
 - crontab添加定时任务，每过6分钟执行一次回帖示例 `*/6 * * * * cd /root/discuz_bot/ && python3 discuz.py` 目录改成自己的

## 说明
 - 自动识别验证码登录
 - 先尝试无验证码登录一次，失败后尝试自动识别验证码登录
 - 针对Hostloc编写，如果是其它Discuz论坛修改一下基本也能用。
