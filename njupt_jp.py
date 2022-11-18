# -*- coding: utf-8 -*-
#   @Time    : 2022/11/7 12:59
#   @Author  : 南国旧梦i
#   @FileName: njupt_jp.py
#   @Software: PyCharm
from datetime import datetime, timedelta, timezone
import hashlib,binascii,random,string
from Crypto.Cipher import AES
import requests

#加密类
class Encrypt:
    #初始化
    def __init__(self, key, iv):
        self.key = key.encode('utf-8')
        self.iv = iv.encode('utf-8')
    #pkcs7 填充方式
    def pkcs7padding(self, text):
        bs = 16
        length = len(text)
        bytes_length = len(text.encode('utf-8'))
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        padding_text = chr(padding) * padding
        self.coding = chr(padding)
        return text + padding_text
    #AES加密
    def aes_encrypt(self, content):
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        content_padding = self.pkcs7padding(content)
        encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
        result = binascii.b2a_hex(encrypt_bytes).decode()
        return result

#登录类
class Login:
    #初始化
    def  __init__(self,username,password):
        self.username = username
        self.password = password
        self.session = requests.session()
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        })
        iv = key= f'iam{int(datetime.timestamp(datetime.now())*1000)}'
        Enc = Encrypt(key=key, iv=iv)
        username,password = Enc.aes_encrypt(username),Enc.aes_encrypt(password)
        self._login(username,password,key)
    #登录
    def _login(self,username,password,key):
        loginUrl= "http://i.njupt.edu.cn/ssoLogin/login"
        data = {
            "username": username,
            "password": password,
            "captcha": "",
            "checkKey": key[3:]
        }
        userInfo = self.session.post(url=loginUrl,data=data).json()
        self.session.get(url="http://i.njupt.edu.cn/cas/login?service=https://evaluation.njupt.edu.cn/base/login/return?type=mobile")
        self.session.get(url="http://i.njupt.edu.cn/cas/granting")
        # print(self.session.get(url="http://i.njupt.edu.cn/cas/granting").text)
        if userInfo["success"]:
            self.log(f'{userInfo["message"]} 学号：{userInfo["result"]["userInfo"]["username"]}  姓名：{userInfo["result"]["userInfo"]["realname"]}\n')
            self._reCourse()
            self.log("所有课程均已完成评价\n")
            return
        else:
            self.log(f'{userInfo["message"]}')
            return
    #获取课程列表
    def _getList(self):
        _jpList = self.session.get(url="https://evaluation.njupt.edu.cn/api/v2/pj/all/list").json()
        return _jpList
    #循环执行课程
    def _reCourse(self):
        cList = self._getList()["data"]
        for c in cList:
            courseid = c["ID"]
            self.log(f'当前评价课程：[{c["COURSENAME"]}]  教学老师：[{c["TEACHERNAME"]}]\n')
            self._doPaper(courseid)
        return
    #提交教评
    def _doPaper(self,courseid):
        self.session.headers.update({
            "Content-Type": "application/json;charset=UTF-8"
        })
        courseUrl= f"https://evaluation.njupt.edu.cn/api/v2/pj/jumpToPaper?id={courseid}"
        resPaper = self.session.get(url=courseUrl).json()
        paperId = resPaper["data"]["paperId"]
        resPaper = resPaper["data"]
        paperUrl = f"https://evaluation.njupt.edu.cn/api/v2/questionnaire/paper/{paperId}"
        verStr = resPaper["commentator"]+resPaper["basicParams"]+resPaper["param1"]+resPaper["param2"]+resPaper["param3"]+resPaper["param4"]+"murp2020"
        verification = self.md5(verStr)
        resQue = self.session.get(url=paperUrl).json()
        answers = {}
        for index,ans in enumerate(resQue["data"]["paperSubjectList"]):
            #表单更新 2022/11/18
            if ans["type"] == 9:
                answers["s"+ans["subjectId"]] = {"result": "A"} if index!=len(resQue["data"]["paperSubjectList"])-2 else {"result": "B"}
        del resPaper["paperId"]
        resPaper.update({
            "deviceId":f"fc1b6ae-{self.randoms(4)}-{self.randoms(3)}",
            "signature":"",
            "status":"1",
            "verification":verification,
            "answers":answers
        })
        res = self.session.post(url=paperUrl,json=resPaper).json()
        return
    def md5(self,str):
        m = hashlib.md5(str.encode('utf-8'))
        return m.hexdigest()

    def getTimeStr(self):
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

    def log(self,content):
        print(self.getTimeStr() + ' ' + str(content))

    def randoms(self,len):
        return ''.join(random.sample(string.ascii_letters + string.digits, len)).lower()



if __name__ == '__main__':
    #开始  学号,密码
    l = Login("12220456**","********")






