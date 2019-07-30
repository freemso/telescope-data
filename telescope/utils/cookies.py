import logging
import random
import re
import time

import pymongo


class Cookies:
    """
    定义cookies的read与update基础行为

    default_cookies_policies = {
        'max_forbidden_count': 3,  # 当接口被封次数达到此数字时，认为该账号已经被暂时封禁
        'use_interval_seconds': 5,  # 每次使用单个cookies需要被冷却的秒数
        'max_validation_days': 30,  # cookie最大有效天数，超过此天数的cookie表明已经失效
        'max_retry_times': 3,  # 取cookie失败时最大重试次数，若超过此重试次数依旧取不到可用cookies则发邮件预警
        'max_waiting_seconds': 5,  # 取cookie时会随机等待一段时间，此值为等待的最大时长
    }
    """

    table = 'cookies'
    logger = logging.getLogger(__name__)

    @classmethod
    def get_cookies(cls, cookies_policies, cookies_type, db):
        """根据策略获取cookies

        :return: (cookies_info, cookies_type)
        """
        try:
            for i in range(0, 1 + cookies_policies['max_retry_times']):
                if i > 0:
                    sleep_seconds = random.uniform(0, cookies_policies['max_waiting_seconds'])
                    cls.logger.debug('sleep %s seconds in get_cookies...', sleep_seconds)
                    time.sleep(sleep_seconds)  # 控制取cookie的延时
                query = {
                    'type': cookies_type,
                    'cooldown': {
                        '$lte': time.time(),
                    },
                    'forbiddenCnt': {
                        '$lt': cookies_policies['max_forbidden_count']
                    },
                    'status': 'USING',
                    # 'usedBy': 'crawler-realtime-api',
                }
                cookies_info = db[cls.table].find_one_and_update(query, {
                    '$set': {
                        'cooldown': time.time() + cookies_policies['use_interval_seconds']
                    },
                    '$inc': {
                        'total_used': 1
                    }
                }, sort=[('cooldown', pymongo.ASCENDING)])
                if cookies_info:
                    cls.logger.info('get %s cookies success at %d times.' % (cookies_type, i + 1))
                    break
                else:
                    cls.logger.warn('get %s cookies failed at %d times.' % (cookies_type, i + 1))

            if cookies_info and cookies_info.get('cookies'):
                return cookies_info['_id'], cookies_info['cookies']
            else:
                if cookies_info:
                    db[cls.table].update({
                        '_id': cookies_info['_id']
                    }, {
                        "$set": {
                            "error": "no cookies field",
                            "status": "LOGIN_FAILED",  # 需要重新登陆获取新的Cookies
                        },
                        "$currentDate": {
                            "updatedAt": True
                        }
                    })
                    cls.logger.error('[%s] has no valid cookies field, marked as LOGIN_FAILED', cookies_info['_id'])
                else:
                    cls.logger.error('no enough %s cookies.' % cookies_type)
                return None, None
        except Exception:
            cls.logger.exception('get cookie error')
            return None, None

    @classmethod
    def update_cookies(cls, cookies_id, cookies_type, response, db):
        if response.status_code in [403]:
            result = db[cls.table].update_one({
                '_id': cookies_id
            }, {
                '$inc': {
                    'forbiddenCnt': 1
                },
                '$currentDate': {
                    'updatedAt': True
                }
            })
            cls.logger.info('update cookies forbiddenCnt[%s]: %s' % (cookies_id, result.raw_result))
        cls._update_cookies_by_type(cookies_id, cookies_type, response, db)

    @classmethod
    def _update_cookies_by_type(cls, cookies_id, cookies_type, response, db):
        extra_update_cookies_type_2_func = {  # update cookies的自定义行为
            '.weibo.cn': cls._update_cookies_weibo_cn
        }
        func = extra_update_cookies_type_2_func.get(cookies_type)
        if func:
            func(cookies_id, response, db)

    @classmethod
    def _update_cookies_weibo_cn(cls, cookies_id, response, db):
        cookies = re.findall(re.compile(r'SUB=([^\s]*?);\s'), str(response.headers))
        if (len(cookies) > 0 and cookies[0] == 'deleted'):  # 当cookies已被服务端被删除，将其cookie时间置为过期
            # update cookies
            result = db[cls.table].update_one({
                '_id': cookies_id
            }, {
                '$set': {
                    'error': 'cookies out of date',
                    'status': 'LOGIN_FAILED',  # 需要重新登陆获取新的Cookies
                },
                '$currentDate': {
                    'updatedAt': True
                }
            })
            cls.logger.info('update cookies out of date[%s]: %s' % (cookies_id, result.raw_result))
            return

        if 'security.weibo.com' in response.url or 'weibo.cn/security' in response.headers.get('Location', ''):  # 账号异常时，置error
            # update cookies
            result = cls.db[cls.table].update_one({
                '_id': cookies_id
            }, {
                '$set': {
                    'error': 'need verify mobile.',
                    'status': 'INVALID',
                },
                '$currentDate': {
                    'updatedAt': True
                }
            })
            cls.logger.info('update cookies invalide[%s]: %s' % (cookies_id, result.raw_result))
            return
