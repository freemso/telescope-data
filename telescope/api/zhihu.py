import logging
from datetime import datetime, timedelta
import requests
from utils.db import DB
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus as urlencode


class ZhihuAPI:
    logger = logging.getLogger(__name__)

    @classmethod
    def explore_answer(cls, topics):
        """按类型获取知乎今日最热"""
        try:
            db = DB.get_crawlerdb()
            secondary_topics = []
            for topic in topics.split(','):
                topic = topic.strip()
                if topic:
                    record = db.zhihutopics.find_one({'topic': topic}, {'secondaryTopics': True})
                    if record:
                        secondary_topics.extend(record['secondaryTopics'])
                        secondary_topics.append(topic)

            if not secondary_topics:
                return []

            answers_cursor = db.cache4zhihuexplore.find({'updatedAt': {'$gt': datetime.now() - timedelta(hours=24)}, 'tags': {'$in': secondary_topics}},
                                                        {'url': True, 'title': True, 'tags': True, 'updatedAt': True}).limit(20)
            answers = []
            for answer in answers_cursor:
                del answer['_id']
                answer['updatedAt'] = str(answer['updatedAt'])
                answers.append(answer)
            return answers
        except Exception:
            cls.logger.exception('explore_answer error.')
            return []

    @classmethod
    def get_monments_by_id(cls, user_id):
        """获取当前用户id的想法列表"""
        def _get_images_list(content_list):
            ret = []
            for content in content_list:
                type = content.get('type', '')
                # 这里type类型有可能是image, text, link, video
                # 其中text只可能是content_list[0]的类型，而link和video的title就是content_list[0]的内容
                # 因此这里只处理image类型的content
                if type == 'image':
                    ret.append(content.get('url', ''))

            return ret

        def _extract_string_title(raw_title):
            if not raw_title:
                return raw_title
            obj_list = ['收起', '查看图片']
            raw_title = raw_title.replace('<br>', '\n')
            soup = BeautifulSoup(raw_title.encode('unicode-escape', 'ignore'), 'lxml')

            for a_tag in soup.find_all('a'):
                for idx, str in enumerate(obj_list):
                    if str in a_tag.get_text():
                        a_tag.extract()

            return soup.get_text().encode().decode('unicode-escape')

        try:
            db = DB.get_crawlerdb()
            url = 'https://api.zhihu.com/pins/{}/moments?limit=20&reverse_order=0'.format(user_id)

            rec = db.variables.find_one({'tag': 'zhihu', 'key': 'Authorization'})
            if not rec or not rec.get('value'):
                raise Exception('fail to get Authorization from db.')

            headers = {
                'Authorization': rec['value'],
                'User-Agent': 'osee2unifiedRelease/4.33.1 (iPhone; iOS 12.1.4; Scale/2.00)',
                'X-API-Version': '4.33.1',
                'x-app-za': 'OS=iOS&Release=12.1.4&Model=iPhone11,8&VersionName=4.33.1&VersionCode=1208&Width=828&Height=1792&DeviceType=Phone&Brand=Apple&OperatorType=46001'
            }
            resp = requests.get(url, headers=headers, timeout=5)
            if not resp or not resp.status_code == 200:
                raise Exception('access zhihu api failed, Authorization may be expired, pls check.')

            pin_list = resp.json().get('data', [])
            parsed_pin_list = []
            for pin in pin_list:
                if not pin.get('type', '') == 'moment' or not pin.get('target'):
                    continue

                target = pin['target']
                url = target.get('url', '')
                author = target.get('author', {}).get('name', '')
                title = ''
                image_urls = []

                if not target.get('content'):
                    raise Exception('content field is null, url: {}'.format(url))

                # 先处理外层内容
                content_list = target['content']
                title = _extract_string_title(content_list[0].get('content', ''))

                if len(content_list) > 1:
                    image_urls = _get_images_list(content_list[1:])

                # 如果是转发的，再加上转发的内容
                if target.get('origin_pin'):
                    origin = target['origin_pin']
                    origin_author = origin.get('author', {}).get('name', '')
                    if not title:
                        title = '转发了'  # 如果是转发且外层title为空，将title设为默认字段

                    if target['origin_pin'].get('is_deleted', False):  # 转发内容已经被删除
                        title = '{}\n\n//@{}: {}'.format(title, origin_author, origin.get('deleted_reason', ''))
                    else:  # 正常解析
                        origin_content_list = origin['content']
                        origin_title = _extract_string_title(origin_content_list[0].get('content', ''))
                        title = '{}\n\n//@{}: {}'.format(title, origin_author, origin_title)
                        if len(origin_content_list) > 1:
                            image_urls += _get_images_list(origin_content_list[1:])

                image_urls = [re.sub(re.compile(r"_.*.jpg"), "_r.jpg", image_url) for image_url in image_urls]
                parsed_pin_list.append({
                    'url': url,
                    'author': author,
                    'title': title,
                    'image_urls': image_urls
                })
            return parsed_pin_list

        except Exception as e:
            cls.logger.exception('get_monments_by_id error. Msg:{}'.format(e))
            return []

    @classmethod
    def _simple_query(cls, url):
        db = DB.get_crawlerdb()
        rec = db.variables.find_one({'tag': 'zhihu', 'key': 'Authorization'})
        if not rec or not rec.get('value'):
            raise Exception('fail to get Authorization from db.')

        headers = {
            'Authorization': rec['value'],
            'User-Agent': 'osee2unifiedRelease/4.33.1 (iPhone; iOS 12.1.4; Scale/2.00)',
            'X-API-Version': '4.33.1',
            'x-app-za': 'OS=iOS&Release=12.1.4&Model=iPhone11,8&VersionName=4.33.1&VersionCode=1208&Width=828&Height=1792&DeviceType=Phone&Brand=Apple&OperatorType=46001'
        }
        resp = requests.get(url, headers=headers, timeout=5)
        if not resp or not resp.status_code == 200:
            raise Exception('access zhihu api failed, Authorization may be expired, pls check.')
        return resp


    @classmethod
    def get_hot_list(cls):
        def _is_valid(idx, item):
            return not 'ad' in item

        def _parse_item(idx, item):
            target = item.get('target')
            if not target:
                return None
            return {
                'id': str(idx),
                'title' : target['title_area']['text'],
                'link' : target['link']['url'],
                'tag' : '',
            }

        try:
            resp = cls._simple_query('https://api.zhihu.com/topstory/hot-list?limit=10&reverse_order=0')
            hot_list = resp.json().get('data', [])
            return [_parse_item(*i) for i in enumerate(hot_list) if _is_valid(*i)]
        except Exception:
            cls.logger.exception('get_hot_list error.')
            return []

    @classmethod
    def get_hot_search(cls):
        def _parse_item(idx, item):
            return {
                'id' : str(idx),
                'title' : item['query_display'],
                'link' : 'https://www.zhihu.com/search?type=content&q={}'.format(urlencode(item['real_query'])),
                'tag' : '',
            }

        try:
            resp = cls._simple_query('https://api.zhihu.com/search/top_search/tabs/hot/items')
            hot_list = resp.json().get('data', [])
            return [_parse_item(*i) for i in enumerate(hot_list)]
        except Exception:
            cls.logger.exception('get_hot_search error.')
            return []
