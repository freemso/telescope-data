import logging
from datetime import datetime, timedelta

import requests

from utils.db import DB

cate_id_map = {
    '24': 'MAD·AMV',
    '25': 'MMD·3D',
    '47': '短片·手书·配音',
    '27': '综合',
    '51': '资讯',
    '169': '布袋戏',
    '170': '资讯',
    '28': '原创',
    '31': '翻唱',
    '30': 'VOCALOID·UTAU',
    '59': '演奏',
    '29': '三次元音乐',
    '54': 'OP/ED/OST',
    '20': '宅舞',
    '154': '三次元舞蹈',
    '156': '舞蹈教程',
    '17': '单机游戏',
    '171': '电子竞技',
    '172': '手机游戏',
    '65': '网络游戏',
    '173': '桌游棋牌',
    '121': 'GMV',
    '136': '音游',
    '19': 'Mugen',
    '37': '纪录片',
    '124': '趣味科普人文',
    '122': '野生技术协会',
    '39': '演讲·公开课',
    '96': '星海',
    '95': '数码',
    '98': '机械',
    '176': '汽车',
    '22': '鬼畜调教',
    '26': '音MAD',
    '126': '人力VOCALOID',
    '127': '教程演示',
    '157': '美妆',
    '158': '服饰',
    '164': '健身',
    '71': '综艺',
    '137': '明星',
    '131': 'Korea相关',
    '138': '搞笑',
    '21': '日常',
    '76': '美食圈',
    '75': '动物圈',
    '161': '手工',
    '162': '绘画',
    '175': 'ASMR',
    '163': '运动',
    '166': '广告',
}


class Bilibili:
    logger = logging.getLogger(__name__)
    proxy_policies = {
        'max_retry_times': 1,
        'proxy_used_interval': 0.1,
        'type': 'bilibili',
        'remember_proxy': False,
        'max_waiting_seconds': 1
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        'Referer': 'https://www.bilibili.com'
    }

    @classmethod
    def cate_search_hot_rank(cls, cate_id, head_size=None, min_play=None, limit=10):
        try:
            url = 'https://s.search.bilibili.com/cate/search'
            params = {
                'main_ver': 'v3',
                'search_type': 'video',
                'view_type': 'hot_rank',
                'pic_size': '160x100',
                'order': 'click',
                'copy_right': '-1',
                'cate_id': cate_id,
                'page': '1',
                'pagesize': '20',
                'time_from': (datetime.utcnow() + timedelta(hours=-48)).strftime('%Y%m%d'),
                'time_to': (datetime.utcnow() + timedelta(hours=-24)).strftime('%Y%m%d'),
            }
            records = requests.get(url, params=params, timeout=3).json()['result']

            result = []
            if head_size is not None and head_size > 0:
                result = records[0:head_size]
            else:
                for record in records:
                    play = int(record['play'])
                    if play >= min_play:
                        result.append(record)

            result = result[0:limit]

            # 入库
            for record in result:
                uid = record['mid']
                new_record = {
                    'source': 'bilibili',
                    'account': uid,
                    'name': record['author'],
                    'reviewStatus': 'NOT_REVIEWED',
                    'pictureUrl': 'https://i2.hdslb.com/bfs/face/60a9153609998b04301dc5b8ed44c41b537a2268.jpg',
                    'createdAt': datetime.now(),
                    'extraInfo': record,
                }

                DB.get_crawlerdb(db_type='jike_internal_tool').crawlercandidatesources.update_one(
                    {'source': 'bilibili', 'account': uid, },
                    {
                        '$inc': {'topNum': 1},
                        '$addToSet': {'vidList': record['id'], 'tags': cate_id_map.get(cate_id, '未知')},
                        '$setOnInsert': new_record,
                    },
                    upsert=True
                )
            return result
        except Exception:
            logging.exception('cate_search_hot_rank error.')
            return None

    @classmethod
    def get_submit_videos(cls, mid, page):
        try:
            url = 'http://space.bilibili.com/ajax/member/getSubmitVideos?mid={}&tid=0&order=senddate&page={}'.format(mid, page)
            r = requests.get(url, headers=cls.headers, timeout=5).json()
            return r
        except Exception:
            cls.logger.exception('get_submit_videos error.')
            return None

    @classmethod
    def search(cls, keywords, page='1'):
        try:
            params = {
                'jsonp': 'jsonp',
                'page': page,
                'search_type': 'video',
                'highlight': '1',
                'keyword': keywords,
                'from_source': 'banner_search',
                'order': 'totalrank',
                'duration': '1',
                'tids': '0',
                'callback': '',  # '__jp1',
            }
            url = 'https://api.bilibili.com/x/web-interface/search/type'
            r = requests.get(url, headers=cls.headers, params=params, timeout=5).json()
            return r
        except Exception:
            cls.logger.exception('search error.')
            return None
