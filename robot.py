# -*- coding: utf-8 -*-
#####################################
#QQ机器人python版本
#2012年12月07日
#Email:lufeng4828@163.com
#####################################
#说明：如果在执行的时候提示ImportError: No module named XXXXX，自己去安装模块，欢迎一起探讨学习
#####################################

import httplib2,urllib
import urllib2 
import random
import time
import threading
import socket
import errno
import os,sys,re,hashlib
import utils
import json.encoder as json_encode
import json.decoder as json_decode
import logging

def Log():
    logger = logging.getLogger()
    hdlr = logging.FileHandler('qqrobot.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s.%(funcName)s Line:%(lineno)d %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger

class QQ(object):
    appid = "8000203"
    def __init__(self,uin,pwd):
        """
        uin:QQ号
        pwd:QQ密码
        """
        self.uin = uin
        self.pwd = pwd
        self.http = httplib2.Http()
        self.loginStatus = False
        self.logger = Log()

    def __initVerifyCode(self):
        """
        初始化验证码
        """
        checkUrl = "http://check.ptlogin2.qq.com/check?uin="+self.uin+"&appid="+self.appid+"&r=0.6315117976338621"
        headers = {"Cookie":"chkuin="+self.uin}
        #请求数据
        response,content = self.http.request(checkUrl,headers=headers)
        pm = re.search(r"ptvfsession=(\w+?);",response["set-cookie"])
        if pm and pm.group(1):
            self.ptvfsession = pm.group(1)
        #判断结果
        m = re.search(r"'(\d)','(.+)','(.+)'", content)
        self.verifyCode1 = m.group(2)
        self.verifyCode2 = m.group(3)
        if m.group(1)=="0":
            print u"免验证码！"
        else:
            print u"需要输入验证码！"
            imgUrl = "http://captcha.qq.com/getimage?aid="+self.appid+"&r=0.3268821237981411&uin="+self.uin
            response,content = self.http.request(imgUrl)

            #如果需要输入验证码，会下载到服务器本地，你需要把code.jpg下载到你的PC机看
            mt = re.search(r"verifysession=(\w+?);",response["set-cookie"])
            if mt and mt.group(1):
                self.verifysession = mt.group(1)
                with open("code.jpg","wb") as img:
                    img.write(content)
                promotStr = "验证码下载完毕("+os.path.split(os.path.realpath(sys.argv[0]))[0]+os.sep+"code.jpg)，请输入："
                self.verifyCode1 = raw_input(promotStr)
            else:
                print u"获取验证码出错！"
    
    def __encodePwd(self):
        """
        对密码加密
        """
        def hex_md5hash(myStr):
            return hashlib.md5(myStr).hexdigest().upper()
        def hexchar2bin(uin):
            uin_final = ''
            uin = uin.split('\\x')
            for i in uin[1:]:
                uin_final += chr(int(i, 16))
            return uin_final
        password_1 = hashlib.md5(self.pwd).digest()
        password_2 = hex_md5hash(password_1 + hexchar2bin(self.verifyCode2))
        password_final = hex_md5hash(password_2 + self.verifyCode1.upper()) 
        self.pwdEncoded = password_final
        
    def __postLogin(self):
        """
        提交网页登录请求，第一次登录
        """
        #GET参数构造
        data = {"u":self.uin}
        data["p"] = self.pwdEncoded
        data["verifycode"] = self.verifyCode1
        data["webqq_type"] = "10"
        data["remember_uin"] = "1"
        data["login2qq"] = "1"
        data["aid"] = self.appid
        data["h"] = "1"
        data["u1"] = "http://web2.qq.com/loginproxy.html?login_level=3"
        data["ptredirect"] = "0"
        data["ptlang"] = "2052"
        data["from_ui"] = "1"
        data["pttype"] = "1"
        data["t"] = "1"
        data["g"] = "1"
        #url编码参数
        body = urllib.urlencode(data)
        #组装GET参数
        loginUrl = "http://ptlogin2.qq.com/login?"+body
        #构造http头，记录Cookie
        headers = {"Cookie":"chkuin="+self.uin+"; confirmuin="+self.uin}
        try:
            headers["Cookie"] += "; verifysession="+self.verifysession
        except AttributeError:
            pass
        try:
            headers["Cookie"] += "; ptvfsession="+self.ptvfsession
        except AttributeError:
            pass
        response,content = self.http.request(loginUrl,headers=headers)
        m = re.search(r"'(\d)','(.+)','(.+)','(.+)','(.+)', '(.+)'", content)
        if m:
            self.loginStatus = True
            self.logger.debug("QQ登录网页成功")
            self.cookie = response["set-cookie"]

    def __get_friend_QQ(self,loginUrl="http://s.web2.qq.com/api/get_friend_uin2",uin=None):
        """
        返回好友QQ号码
        """
        #GET参数构造 
        loginUrl = "%s?tuin=%s&verifysession=&type=1&code=&vfwebqq=%s" % (loginUrl,uin,self.vfwebqq)
        #请求数据
        request = urllib2.Request(loginUrl,headers=self.headers)
        response = urllib2.urlopen(request)  
        #读取结果
        ret = response.read()  
        self.logger.debug("返回好友信息:%s" % ret)
        #返回的结果是字符串格式的json，要用json解析
        ret = json_decode.JSONDecoder().decode(ret)
        return ret

    def __get_group_QQ(self,loginUrl="http://s.web2.qq.com/api/get_friend_uin2",gin=None):
        """
        返回QQ群号码
        """
        #GET参数构造
        loginUrl = "%s?tuin=%s&verifysession=&type=4&code=&vfwebqq=%s" % (loginUrl,gin,self.vfwebqq)
        #请求数据
        request = urllib2.Request(loginUrl,headers=self.headers)
        response = urllib2.urlopen(request)  
        #读取结果
        ret = response.read()  
        self.logger.debug("返回Q群信息:%s" % ret)   
        #返回的结果是字符串格式的json，要用json解析
        ret = json_decode.JSONDecoder().decode(ret)
        return ret

    def __send_msg_to_friend(self,loginUrl="http://d.web2.qq.com/channel/send_buddy_msg2",friend_info=None,msg=None):
        """
        给好友发消息
        """
        if any([friend_info == None,msg == None]):
            return {"retcode":-1,"result":"no"}   
        self.fmsg_id += 1
        #组装POST参数
        r = {"to":friend_info['uin'],"face":friend_info['face'],"content":"[%s,\"\\n【消息来自明朝机器人】\",[\"font\",{\"name\":\"微软雅黑\",\"size\":\"9\",\"style\":[0,0,0],\"color\":\"ff0000\"}]]" % msg,"msg_id":self.fmsg_id,"clientid":int(self.clientid),"psessionid":self.psessionid}
        post_data_dic = {'r':json_encode.JSONEncoder().encode(r),'clientid':int(self.clientid),'psessionid':self.psessionid}
        #url编码，否则解析不了
        post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
        #请求数据
        request = urllib2.Request(loginUrl,post_encode, self.headers)
        response = urllib2.urlopen(request)  
        #读取结果
        ret = response.read()  
        self.logger.debug("给好友发送信息结果:%s" % ret)   
        #返回的结果是字符串格式的json，要用json解析
        ret = json_decode.JSONDecoder().decode(ret)
        try:
            if int(ret["retcode"]) == 121:
                self.loginStatus = False
        except:
            pass
        return ret

    def __send_msg_to_group(self,loginUrl="http://d.web2.qq.com/channel/send_qun_msg2",group_info=None,msg=None):
        """
        给群发消息
        """
        if any([group_info == None,msg == None]):
            return {"retcode":-1,"result":"no"} 
        self.gmsg_id += 1
        #构造消息体
        r = {"group_uin":group_info['group_uin'],"content":"[%s,\"\\n【消息来自明朝机器人】\",[\"font\",{\"name\":\"微软雅黑\",\"size\":\"9\",\"style\":[0,0,0],\"color\":\"ff0000\"}]]" % msg,"msg_id":self.gmsg_id,"clientid":int(self.clientid),"psessionid":self.psessionid}
        post_data_dic = {'r':json_encode.JSONEncoder().encode(r),'clientid':int(self.clientid),'psessionid':self.psessionid}
        #url编码
        post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
        #请求对象
        request = urllib2.Request(loginUrl,post_encode, self.headers)
        response = urllib2.urlopen(request)  
        #读取返回结果
        ret = response.read()  
        self.logger.debug("给Q群发送信息结果:%s" % ret)   
        #返回的结果是字符串格式的json，要用json解析
        ret = json_decode.JSONDecoder().decode(ret)
        try:
            if int(ret["retcode"]) == 121:
                self.loginStatus = False
        except:
            pass
        return ret

    def __get_friend_info2(self,loginUrl="http://s.web2.qq.com/api/get_user_friends2"):
        """
        获取好友信息
        """
        #构造POST参数
        r = {"h":"hello","vfwebqq":self.vfwebqq}
        post_data_dic = post_data_dic = {'r':json_encode.JSONEncoder().encode(r)}
        #对POST参数进行url编码
        post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
        #生成请求对象
        request = urllib2.Request(loginUrl,post_encode, self.headers)
        response = urllib2.urlopen(request)  
        #读取返回结果，并解析Json数据
        ret = response.read()
        ret = json_decode.JSONDecoder().decode(ret)
        #好友的两个数据格式
        self.friend_info1 = {}
        self.friend_info2 = {}
        #self.friend_info1只包含有uin信息，不是QQ号码，但是通过这个我们可以请求服务器得到QQ号码
        for item in ret['result']['info']:
            self.friend_info1.update({item['uin']:[item['nick'],item['face']]})
        for k,v in self.friend_info1.items():
            #获取QQ号码
            qqret = self.__get_friend_QQ(uin=k)
            if qqret["retcode"] == 0:
                self.friend_info2.update({qqret['result']['account']:[k,v[0],v[1]]})

        print "当前好友列表如下:"
        print "#" * 50
        print "QQ号码\t\t昵称"
        
        for k,v in self.friend_info2.items():
            print "%s\t%s" % (k,v[1])
        print "#" * 50 
        print

    def __get_group_info2(self,loginUrl="http://s.web2.qq.com/api/get_group_name_list_mask2"):
        """
        获取QQ群信息
        """
        #构造POST参数
        r = {"vfwebqq":self.vfwebqq}
        post_data_dic = post_data_dic = {'r':json_encode.JSONEncoder().encode(r)}
        post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
        #生成请求对象
        request = urllib2.Request(loginUrl,post_encode, self.headers)
        response = urllib2.urlopen(request)  
        #读取返回结果，并解析Json数据
        ret = response.read()
        ret = json_decode.JSONDecoder().decode(ret)
        #好友的两个数据格式
        self.group_info1 = {}
        self.group_info2 = {}
        #self.group_info1这个里面没有群号码，但是需要里面的gin来向服务器请求群号码
        for item in ret['result']['gnamelist']:
            self.group_info1.update({item['gid']:[item['name'],item['code']]})
        for k,v in self.group_info1.items():
            #获取qq群号码
            qunret = self.__get_group_QQ(gin=v[1])
            if qunret["retcode"] == 0:
                self.group_info2.update({qunret['result']['account']:[k,v[0],v[1]]})

        print "当前QQ群列表如下:"
        print "#" * 50
        print "QQ群号码\t名称"

        for k,v in self.group_info2.items():
            print "%s\t%s" % (k,v[1])
        print "#" * 50 
        print 

    def __real_login(self,loginUrl="http://d.web2.qq.com/channel/login2"):
        """
        真正的登录才刚刚开始,向腾讯服务器登录QQ
        """
        if hasattr(self,'cookie') and self.loginStatus:
            cookies = re.split(r';[, ]*',self.cookie)
            #初始化http头
            self.headers = {}
            self.headers["Cookie"] = self.cookie
            self.headers["User-Agent"] = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)"
            self.headers["Referer"] = "http://d.web2.qq.com/proxy.html?v=20110331002&callback=1&id=2"
            #获取ptwebqq、psessionid、vfwebqq等重要信息
            for ck in cookies:
                if ck and ck.split('=')[0] == 'ptwebqq':
                    self.clientid = random.randrange(10000000,19999999)
                    r = {'status':'online','ptwebqq':ck.split('=')[1],'passwd_sig':'','clientid':self.clientid,'psessionid':'null'}
                    post_data_dic = {'r':json_encode.JSONEncoder().encode(r),'clientid':self.clientid,'psessionid':'null'}
                    post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
                    #生成请求对象
                    request = urllib2.Request(loginUrl,post_encode, self.headers)
                    response = urllib2.urlopen(request)  
                    #读取返回结果，并解析Json数据
                    ret = response.read()
                    ret = json_decode.JSONDecoder().decode(ret)
                    #初始化重要变量
                    self.psessionid = ret['result']['psessionid']
                    self.vfwebqq = ret['result']['vfwebqq']
                    #retcode为0则登录成功
                    if ret['retcode'] == 0:
                        self.logger.debug("登录腾讯服务器成功")   
                        print "登录成功！"
                   
    def __poll2_(self,loginUrl="http://d.web2.qq.com/channel/poll2",ids=None):
        """
        循环调用这个函数，这个函数是用来接收信息的，比如好友信息、群消息、好友上线或者下线消息等等
        """
        #构造POST参数
        r = {"clientid":str(self.clientid),"psessionid":self.psessionid,"key":0,"ids":ids}
        post_data_dic = {'r':json_encode.JSONEncoder().encode(r),'clientid':int(self.clientid),'psessionid':self.psessionid}
        #对POST参数进行url编码
        post_encode = urllib.urlencode(post_data_dic).encode("utf-8")
        #生成请求对象
        request = urllib2.Request(loginUrl,post_encode, self.headers)
        response = urllib2.urlopen(request)  
        #读取返回结果，并解析Json数据
        ret = response.read()
        self.logger.debug("WebQQ收到消息:%s" % ret)   
        ret = json_decode.JSONDecoder().decode(ret)
        #后面可以对这个信息处理从而实现接收信息
        return ret

    def __get_msg_tip2_(self):
        """
        也不知道是什么，反正一直请求，大概是一些消息到来的提示，和poll2一样一直需要请求
        """
        #初始化http头
        self.headers['Referer'] = "http://webqq.qq.com/"
        #一些参数构造
        self.__rc += 1
        num = 100 + self.__rc
        #生成随机值
        t = '%s' % '%d' % time.time() + '%s' % num
        #构造url
        loginUrl = 'http://webqq.qq.com/web2/get_msg_tip?uin=&tp=1&id=0&retype=1&rc='+'%s'% self.__rc +'&lv=3&t=' + t
        #生成请求对象
        request = urllib2.Request(loginUrl,headers=self.headers)
        response = urllib2.urlopen(request)  
        #读取返回结果，并解析Json数据
        ret = response.read()
        self.logger.debug("Web QQ收到tip信息:%s" % ret)   
        ret = json_decode.JSONDecoder().decode(ret)
        return ret

    def __poll2(self):
        #写一个线程来循环请求
        ids = []
        while 1:
            try:
                poll_ret = self.__poll2_(ids=ids)
                print poll_ret
                #获取发消息类型
                poll_type = poll_ret['result'][0]['poll_type']
                from_uin = poll_ret['result'][0]['value']['from_uin']
                self.logger.debug("poll_type=%s,from_uin=%s" % (poll_type,from_uin)) 
                if poll_type == "group_message" and from_uin == self.group_info2[250171844][0]:
                    #获取发消息的内容
                    content = poll_ret['result'][0]['value']['content'][1]
                    rnd = random.randrange(1,135)
                    mtext = "[\"face\",%d],\"%s\\n\"" % (rnd,"robot冒泡下...")
                    if rnd < 5:
                        self.__send_msg_to_group(group_info={'group_uin':from_uin},msg=mtext)
                elif poll_type == "message":
                    rnd = random.randrange(1,135)
                    mtext = "[\"face\",%d],\"%s\\n\"" % (rnd,random.choice(self.mdata))
                    self.__send_msg_to_friend(friend_info={'uin':from_uin,'face':self.friend_info1[from_uin][1]},msg=mtext)
                else:
                    pass
                ids = [str(poll_ret['result'][0]['value']['msg_id'])]
            except Exception,error:
                self.logger.debug("%s" % error)   
            time.sleep(3)

    def __get_msg_tip2(self):
        #写一个线程来循环请求
        while 1:
            try: 
                tip_ret = self.__get_msg_tip2_()
            except Exception,error:
                self.logger.debug("%s" % error) 
            time.sleep(10)

    def login(self):
        #WebQQ网页验证是否需要输入验证码
        self.__initVerifyCode()

        #加密密码
        self.__encodePwd()

        #第一步登录WebQQ网页部分
        self.__postLogin()
        
        #第二部登录腾讯QQ服务器部分
        self.__real_login()

        #获取好友信息
        self.__get_friend_info2()

        #获取QQ群信息
        self.__get_group_info2()

        #初始化一些变量
        self.__rc = 0
        self.mdata = open('mdb.dat').read().strip().split('\n')
        self.gmsg_id = random.randrange(10000000,19999999)
        self.fmsg_id = random.randrange(10000000,19999999)
        self.std_key = "44438c8f5db1c85862e6aa223c54c3e6ee3e7d86"

        #初始化两个线程来处理长连接，用于接收来自服务器的消息
        backend_proc = []
        #接收消息线程
        backend_proc.append(threading.Thread(target=self.__poll2,args=()))
        #接收提示信息线程
        backend_proc.append(threading.Thread(target=self.__get_msg_tip2,args=()))
        for proc in backend_proc:
            #主进程退出以后线程也自动退出
            proc.setDaemon(True)
            #执行线程
            proc.start()

        reciver =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #设置端口可以直接使用不用等待
        reciver.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        reciver.bind(('0.0.0.0',51234))
        reciver.listen(5)
        print "开始接收消息！"
        while 1:
            mtype,id,key,mtext = 'G',0,'',''
            #获取从8888端口过来的消息，消息的格式为:Type#@#Msg，Type代表有S和G两个值，分别代表发给个人和发给QQ群
            connection,address = reciver.accept()  
            try:
                self.logger.debug("loginStatus [%s]" % str(self.loginStatus))
                connection.settimeout(10)
                if self.loginStatus:
                    self.logger.debug("ready [ok]")
                    connection.send('ready')
                else:
                    self.logger.debug("ready [no]")
                    connection.send('no')
                msg = connection.recv(1024) 
                self.logger.debug("接收到8888端口信息：%s" % str(msg)) 
                try:
                    mtype,id,key,mtext = msg.split("#@#")
                    id = int(id)
                except Exception,error:
                    self.logger.debug("msg.split发生错误:%s" % str(error))
                    continue

                if key != self.std_key:
                    connection.send('-2')
                    continue

                if mtype == 'S' and id not in self.friend_info2:
                    connection.send('-1')
                    continue
                elif mtype == 'G' and id not in self.group_info2:
                    connection.send('-1')
                    continue
                else:
                    connection.send('1')
            except socket.timeout:
                self.logger.debug("连接超时")
            connection.close()

            try:
                mtype,mtext = msg.split("#@#")
            except Exception:
                pass
            mtext = mtext.replace("\n","\\n")
            #发送消息，根据mtype的值执行对应的函数，如果是G，则执行第一个，即发群消息
            if mtype == 'G':
                ret = self.__send_msg_to_group(group_info={'group_uin':self.group_info2[id][0]},msg="\"%s\"" % mtext)
            else:
                ret = self.__send_msg_to_friend(friend_info={'uin':self.friend_info2[id][0],'face':self.friend_info2[id][2]},msg="\"%s\"" % mtext)
        
            time.sleep(1)

class QqDaemon(utils.Daemon):
    def __init__(self,pidfile,prog_dir,qq,pswd):
        self.qq = qq
        self.pswd = pswd
        self.prog_dir = prog_dir
        self.pidfile = pidfile
        super(QqDaemon,self).__init__(self.pidfile,self.prog_dir)

    def _run(self):
        robot = QQ(self.qq,self.pswd)
        robot.login()
 
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == 'start': 
        qq = str(raw_input('QQ号: '))
        pswd = str(raw_input('QQ密码: '))
        __qq = qq.strip()                                                                                                                             
        __pswd = pswd.strip()
    else:
       __qq = 0
       __pswd = 0
    prog_dir = os.getcwd()
    daemon = QqDaemon('/var/run/qqrobot.pid',prog_dir,__qq,__pswd)
    if len(sys.argv) == 2:
        try:
            {'start':daemon.start,
             'stop':daemon.stop,
            }[sys.argv[1]]()
        except KeyError,e:
            print "unknow parameter!!!"
            sys.exit(2)
        sys.exit(0)
    else:
        print 'usage: %s start|stop' % sys.argv[0]
        sys.exit(2) 
