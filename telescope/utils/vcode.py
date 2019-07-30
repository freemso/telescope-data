import json
import time

import requests


class VCode:
    apiurl = 'http://api.yundama.com/api.php'
    username = 'jikecrawler'
    password = 'JsaWNlbn'
    appid = '4797'
    appkey = '6ea1f7814ae9dc816b2b8619dc7b2300'
    default_codetype = 1004

    @classmethod
    def request(cls, fields, files=[]):
        response = cls.post_url(cls.apiurl, fields, files)
        response = json.loads(response)
        return response

    @classmethod
    def upload(cls, image, codetype, timeout):
        data = {'method': 'upload', 'username': cls.username, 'password': cls.password, 'appid': cls.appid, 'appkey': cls.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': image}
        response = cls.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    @classmethod
    def result(cls, cid):
        data = {'method': 'result', 'username': cls.username, 'password': cls.password, 'appid': cls.appid, 'appkey': cls.appkey, 'cid': str(cid)}
        response = cls.request(data)
        return response and response['text'] or ''

    @classmethod
    def decode(cls, image, codetype, timeout):
        cid = cls.upload(image, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = cls.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''

    @classmethod
    def report(cls, cid):
        data = {'method': 'report', 'username': cls.username, 'password': cls.password, 'appid': cls.appid, 'appkey': cls.appkey, 'cid': str(cid), 'flag': '0'}
        response = cls.request(data)
        if (response):
            return response['ret']
        else:
            return -9001

    @classmethod
    def post_url(cls, url, fields, files=[]):
        res = requests.post(url, files=files, data=fields, timeout=10)
        return res.text

    @classmethod
    def get_vcode(cls, image, codetype=None):
        """
        根据图片返回验证码
        验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
        """
        if codetype is None:
            codetype = cls.default_codetype

        # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
        cid, result = cls.decode(image, codetype, timeout=10)
        return {'ret': 0, 'result': result, 'cid': cid} if cid > 0 else {'ret': 500, 'result': '', 'cid': cid}
