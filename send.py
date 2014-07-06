#coding:utf-8
import os
import socket
import hashlib
import time
import optparse
import sys
import random

reload(sys)
sys.setdefaultencoding('utf8')

usage = "%prog [option] <message>"
parser = optparse.OptionParser(usage=usage)
parser.add_option('-u','--user',
                  default=0,
                  dest='user',
                  help=("输入要发送信息的QQ号码,个可以通过','号分隔")
                 )

parser.add_option('-h','--host',
                  default="127.0.0.1",
                  dest='host',
                  help=("输入webqq程序运行的ip地址，多个通过逗号分隔")
                 )

parser.add_option('-g','--group',
                  default=0,
                  dest='group',
                  help=("输入要发送信息的QQ群,多个可以通过','号分隔")
                 )

parser.add_option('-k','--key',
                  default=0,
                  dest='key',
                  help=("输入发信授权key")
                 )

#获取参数
options,args = parser.parse_args()

if not args:
    parser.print_help()
    os._exit(1)

#获取选项
_opts = {}
for k,v in options.__dict__.items():
    _opts[k] = v

#必须要带上的选项
users = _opts['user']
groups = _opts['group']
key = _opts['key']
hosts = _opts['host']

#获取授权key的sha1摘要
sha1 = hashlib.sha1()
sha1.update(str(key))
enkey = sha1.hexdigest()

#如果都没有加上任何选项则退出
if users == 0 and groups == 0:
    parser.print_help()
    os._exit(1)
message = ''.join(args)

serv_urls = host.split(',')
if users:
    url = random.choice(serv_urls)
    for user in users.split(","):
        usender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            usender.connect(url)
            data = usender.recv(512)
        except socket.error:
            data = 'no' 
        if data != 'ready':
            url = random.choice([i for i in serv_urls if i != url])
            usender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                usender.connect(url)
                data = usender.recv(512)
            except socket.error:
                data = 'no' 
            if data != 'ready':
                continue
        usender.send('S#@#%s#@#%s#@#%s' % (user,enkey,message))
        ret = usender.recv(1024)
        print {"-1":"QQ号:%s不存在！" % user,
               "-2":"发送消息到%s授权失败，key不正确！" % user,
               "1":"发送消息到%s成功！" % user
              }[ret]
        usender.close()

#发送群消息，如果有的话
if groups:
    url = random.choice(serv_urls)
    for group in groups.split(","):
        gsender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            gsender.connect(url)
            data = gsender.recv(512)
        except socket.error:
            data = 'no'
        if data != 'ready':
            url = random.choice([i for i in serv_urls if i != url])
            gsender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                gsender.connect(url)
                data = gsender.recv(512)
            except socket.error:
                data = 'no'
            if data != 'ready':
                continue
        gsender.send('G#@#%s#@#%s#@#%s' % (group,enkey,message))
        ret = gsender.recv(1024)
        print {"-1":"QQ群:%s不存在！" % group,
               "-2":"发送消息到群%s授权失败，key不正确！" % group,
               "1":"发送消息到群%s成功！" % group
              }[ret]
        gsender.close()
