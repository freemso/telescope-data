import logging

import requests


class DoubanAPI:
    logger = logging.getLogger(__name__)

    @classmethod
    def get_user_info(cls, uid):
        """获得用户基本信息"""
        url = "https://api.douban.com/v2/user/{}".format(uid)
        r = requests.get(url, timeout=10)
        return r.json()

    @classmethod
    def get_life_stream(cls, uid, count=100, raw=False):
        """动态"""
        params = {
            'slice': 'recent-2018-10',
            'hot': 'false',
            'count': count,
            'ck': '2oMs',
            'for_mobile': 1
        }
        headers = {
            'Accept': 'application/json',
            'Referer': 'https://m.douban.com/people/{}/'.format(uid),
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36',
            'Host': 'm.douban.com'
        }
        url = "https://m.douban.com/rexxar/api/v2/user/{}/lifestream".format(uid)
        r = requests.get(url, params=params, headers=headers, timeout=10)
        raw_result = r.json()

        if raw:
            return raw_result
        else:
            events = []
            for item in raw_result["items"]:
                if item["type"] == "subjects":
                    # 标记了多个
                    for subject in item["content"]["subjects"]:
                        event = {
                            'time': item['time'],
                            'activity_type': 'mark',  # 标记书影音
                            'activity': item['activity'],  # 在读、读过、想读
                            'url': subject['url'],  # 书影音的链接
                            'title': subject['title'],  # 书影音的标题
                            'rating': "%.1f分" % subject['rating']['value'],
                            'pic': subject['pic']['normal'],
                            'type': subject['type']  # book, movie, tv, music
                        }
                        events.append(event)
                elif item['type'] == 'card':
                    # 标记了一个
                    content = item["content"]
                    event = {
                        'time': item['time'],
                        'activity_type': 'mark',  # 标记书影音
                        'activity': item['activity'],  # 在读、读过、想读
                        'url': item['url'],  # 书影音的链接
                        'title': content['title'],  # 书影音的标题
                        'rating': content['description'].split("/")[0],
                        'pic': content['cover_url'],
                        'type': content.get("type", "unknown")  # book, movie, tv, music
                    }
                    events.append(event)
                elif item['type'] == 'status':
                    # 发广播
                    content = item['content']
                    event = {
                        'time': item['time'],
                        'activity_type': 'status',  # 发广播
                        'activity': item['activity'],  # 发广播
                        'text': content['text'],  # 动态文字内容
                        'images': [i["normal"]["url"] for i in content["images"]]
                    }
                    events.append(event)
            return events
