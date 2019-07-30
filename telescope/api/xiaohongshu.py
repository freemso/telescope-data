import hashlib
import json
import logging
import re
import time
from urllib import parse

import pymongo
import requests
from bson.objectid import ObjectId

import execjs
from utils.db import DB


class XiaoHongShuApi:
    logger = logging.getLogger(__name__)

    headers_pc = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        'Referer': 'https://www.xiaohongshu.com'

    }

    headers_ios = {
        'device_id': '3371E41A-E744-4AAE-AA8D-1A10747A5DA7',
        'User-Agent': 'discover/5.26.2 (iPhone; iOS 12.0; Scale/2.00) Resolution/750*1334 Version/5.26.2 Build/5262027 Device/(Apple Inc.;iPhone9,3) NetType/Unknown',
    }

    host = 'https://www.xiaohongshu.com'
    template_search_object_id = ObjectId('5a5eee0bb9b8d3016198abd0')
    template_user_notes_object_id = ObjectId('5a5ef08db9b8d3016198abd1')

    proxy_policies = {
        'max_retry_times': 1,
        'proxy_used_interval': 2,
        'type': '.xiaohongshu.com',
        'remember_proxy': False,
        'max_waiting_seconds': 1,
    }

    crawler_db_name = 'crawler'

    def get_sign(params):
        def __md5hex(word):
            word = word.encode('utf-8')
            m = hashlib.md5()
            m.update(word)
            return m.hexdigest()

        key = ''
        for k, val in params.items():
            key = key + k + '%3D' + val
        deviceid = params['deviceId']
        v1_2 = bytearray(key, 'utf-8')
        v5_1 = ''
        v3_2 = 0
        v2 = 0
        v4_1 = bytearray(deviceid, 'utf-8')

        while v2 < len(v1_2):
            v5_1 = v5_1 + str(v1_2[v2] ^ v4_1[v3_2])
            v3_2 = (v3_2 + 1) % len(v4_1)
            v2 = v2 + 1

        sign = __md5hex(__md5hex(v5_1) + deviceid)
        return sign

    @classmethod
    def get_page_by_url(cls, url):
        try:
            _at = cls.get_field_at_from_abdr(cls.headers_pc['User-Agent'], url, cls.headers_pc['Referer'])
            if not _at:
                cls.logger.exception('get _at failure. _at[{}]'.format(_at))
                return None

            url = '{}?_at={}'.format(url, _at)
            resp = requests.get(url, headers=cls.headers_pc, timeout=5)
            cookies = resp.cookies.get_dict()
            resp = requests.get(url, headers=cls.headers_pc, cookies=cookies, timeout=5)
            page_json = json.loads(re.findall(re.compile(r'window.__INITIAL_SSR_STATE__=(\{.*\}})</script>'), resp.text)[0])
            return page_json
        except Exception:
            cls.logger.exception('get_note error.')
            return None

    @classmethod
    def get_res_from_db(cls, key):
        try:
            db = DB.get_crawlerdb(cls.crawler_db_name)
            rec_col = db.xiaohongshushield.find_one(
                {
                    'key': key
                }
            )
            if not rec_col:
                return None

            params = rec_col['params']
            url = rec_col['url']
            headers = dict({
                'shield': rec_col['shield']
            }, **cls.headers_ios)
            page_json = requests.get(url, headers=headers, params=params, timeout=3).json()

            if page_json.get('success') is False:  # 当访问没有问题参数有问题时，打印返回的错误信息
                cls.logger.warning(page_json)
                return None
            else:
                return page_json
        except Exception:
            cls.logger.exception('get_res_from_db error. key: {}.'.format(key))
            return None

    @classmethod
    def search_notes(cls, keyword):
        return cls.get_res_from_db(keyword)

    @classmethod
    def get_user_notes(cls, userid):
        return cls.get_res_from_db(userid)

    @classmethod
    def get_note(cls, url):
        return cls.get_page_by_url(url)

    @classmethod
    def get_shield(cls, count):
        try:
            mongo_db = DB.get_crawlerdb(cls.crawler_db_name)

            cursor = mongo_db.rule.find(
                {
                    'template':
                    {
                        "$in": [
                            cls.template_search_object_id,
                            cls.template_user_notes_object_id
                        ]
                    },
                    'status': 'RUN'
                },
                {
                    'meta.parameters': True,
                    'dataUpdatedAt': True,
                    'template': True,
                    '_id': True
                },
                limit=int(count),
                sort=[('dataUpdatedAt', pymongo.ASCENDING)]
            )

            if not cursor:
                return None

            device_id = '3371E41A-E744-4AAE-AA8D-1A10747A5DA7'
            device_fingerprint = '20171002033735557f8bbe281a61121198ebb083173a8801b14c8e1ff83ec3'
            sid_col = mongo_db.variables.find_one({'tag': 'xiaohongshu', 'key': 'sid'})
            if not sid_col or not sid_col.get('value', ''):
                return None
            sid = 'session.{}'.format(sid_col['value'])

            ret = []
            updated_rules = []
            for data in cursor:
                updated_rules.append(data['_id'])
                if data['template'] == cls.template_user_notes_object_id:
                    # usernote
                    userid = data['meta']['parameters'][0].strip()
                    params = {
                        'deviceId': device_id,
                        't': str(int(time.time())),
                        'lang': 'zh-Hans',
                        'sub_tag_id': '',
                        'platform': 'iOS',
                        'device_fingerprint': device_fingerprint,
                        'sid': sid,
                        'size': 'l',
                        'page': '1',
                        'device_fingerprint1': device_fingerprint,
                        'page_size': '15',
                    }
                    params['sign'] = cls.get_sign(dict(sorted(params.items())))
                    path = '/api/sns/v3/note/user/{}'.format(userid)
                    ret.append({
                        'id': userid,
                        'params': params,
                        'path': path,
                    })
                else:
                    # search
                    keyword = data['meta']['parameters'][0].strip()
                    params = {
                        'deviceId': device_id,
                        'keyword': parse.quote(keyword),
                        'device_fingerprint': device_fingerprint,
                        'device_fingerprint1': device_fingerprint,
                        'keyword_type': 'normal',
                        'lang': 'zh',
                        'page': '1',
                        'page_size': '20',
                        'platform': 'iOS',
                        'sid': sid,
                        'sort': 'general',
                        't': str(int(time.time())),
                        'width': '320',
                        'search_id': '',
                        'source': 'explore_feed',
                    }

                    params['sign'] = cls.get_sign(dict(sorted(params.items())))
                    params['keyword'] = keyword  # 复原URLeEncode前的keyword

                    path = '/api/sns/v8/search/notes'
                    ret.append({
                        'id': '',
                        'params': params,
                        'path': path,
                    })

            # 更新dataUpdatedAt字段
            mongo_db.rule.update_many(
                {
                    '_id':
                    {
                        "$in": updated_rules
                    }
                },
                {
                    '$currentDate':
                    {
                        'dataUpdatedAt': True
                    }
                }
            )
            return ret
        except Exception:
            cls.logger.exception('get_shield error.')
            return None

    @classmethod
    def upload_shield(cls, data):
        task_list = data.split('$$')
        task_cnt = 0
        try:
            mongo_db = DB.get_crawlerdb(cls.crawler_db_name)
            for task in task_list:
                params_list = task.split('##')
                record = {
                    'params': {}
                }
                for p in params_list:
                    k, v = p.split('=')
                    if k == 'id':
                        record['key'] = v
                    elif k == 'path':
                        record['url'] = cls.host + v
                    elif k == 'shield':
                        record['shield'] = v
                    else:
                        record['params'][k] = v

                # 如果id为空，说明是搜索接口，将keyword置为key
                if not record['key']:
                    record['key'] = record['params']['keyword']

                # 写入数据库
                mongo_db.xiaohongshushield.update_one(
                    {
                        'key': record['key']
                    },
                    {
                        '$set':
                        {
                            'url': record['url'],
                            'params': record['params'],
                            'shield': record['shield']
                        },
                        '$currentDate': {'updatedAt': True}
                    },
                    upsert=True
                )

                task_cnt += 1

            return {'count': task_cnt}
        except Exception:
            cls.logger.exception('upload shield error.')
            return None

    @classmethod
    def get_topic_notes(cls, topicid, filter_note_type, page=1):
        """
        topic发文列表页

        filter_note_type: all|所有类型的消息
        filter_note_type: multi|长笔记
        filter_note_type: normal|普通文章
        filter_note_type: video|视频
        """
        try:
            page = int(page)
            result = []
            url = 'https://www.xiaohongshu.com/web_api/sns/v1/page/{}/notes?page={}&page_size=20'.format(topicid, page)
            r = requests.get(url, headers=cls.headers_pc, timeout=5).json()
            data = r.get('data')
            for e in data:
                if filter_note_type == 'all' or e.get('type') == filter_note_type:
                    result.append(e)
            return result
        except Exception:
            cls.logger.exception('get_topic_notes error.')
            return None

    @classmethod
    def get_user_profile(cls, userid):
        try:
            url = 'https://www.xiaohongshu.com/user/profile/{}'.format(userid)
            return cls.get_page_by_url(url)
        except Exception:
            cls.logger.exception('get_user_profile error.')
            return None

    @classmethod
    def get_field_at_from_abdr(cls, ua, url, referer):
        try:
            url_anti_bot_baidu = 'https://anti-bot.baidu.com/abdr'
            with open('js/xhs.js', 'r') as file:
                js_script = file.read()
            ctx = execjs.compile(js_script)
            paylaod_anti_bot_baidu = ctx.call('at', ua, url, referer, True)
            resp_anti_bot_baidu = requests.post(url_anti_bot_baidu, data=paylaod_anti_bot_baidu, timeout=5).text
            _at = resp_anti_bot_baidu.split('|')[0]
            return _at
        except Exception:
            cls.logger.exception('get _at from baidu anti bot failed.')
            return None
