import logging
import re
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from requests import RequestException

from utils.cookies import Cookies
from utils.db import DB


class WeiboAPI:
    logger = logging.getLogger(__name__)
    cookies_type = '.weibo.cn'

    BASE_URL = 'https://m.weibo.cn/api/container/getIndex'

    cookies_policies = {
        'max_waiting_seconds': 1,
        'max_validation_days': 9999,
        'max_retry_times': 2,
        'max_forbidden_count': 5,
        'type': cookies_type,
        'use_interval_seconds': 0.001,
    }

    @staticmethod
    def weibo_text(raw_text):
        """处理微博接口text字段"""
        soup = BeautifulSoup(raw_text, "lxml")
        for a in soup.select('a[data-url]'):
            if a.select('img[src*="timeline_card_small_location_default"]'):
                a.insert_before('📍')
            else:
                real_link = ""
                data_url = a.get("data-url", "")
                href = a.get("href", "")
                if data_url.startswith("/") or data_url.startswith("http"):
                    real_link = data_url
                elif href.startswith("/") or href.startswith("http"):
                    real_link = href

                if real_link:
                    link_params = parse_qs(urlparse(real_link).query)
                    if link_params.get("url"):
                        real_link = link_params["url"][0]
                    elif link_params.get("target"):
                        real_link = link_params["target"][0]
                    elif link_params.get(""):
                        real_link = link_params[""][0]

                    a.string = (" https://m.weibo.cn%s " if real_link[0] == "/" else " %s ") % real_link

        for img in soup.select('img[src*="//h5.sinaimg.cn/m/emoticon/icon"]'):
            img_alt = img.get("alt")
            if img_alt:
                img.insert_before(img_alt)

        # 使用换行符分行
        for br in soup.find_all("br"):
            br.replace_with("\linebreak")
        result_text = soup.text.replace("\n", "").replace("\linebreak", "\n")

        emoji_map = {
            "[坏笑]": "😏", "[舔屏]": "😍", "[污]": "🙈", "[微笑]": "😃", "[嘻嘻]": "😁", "[可爱]": "😊",
            "[吃惊]": "😱", "[害羞]": "☺️", "[挤眼]": "😜", "[闭嘴]": "🤫", "[鄙视]": "😒", "[爱你]": "😘", "[泪]": "😭",
            "[偷笑]": "😉", "[亲亲]": "😚", "[生病]": "😷", "[感冒]": "😷", "[太开心]": "😁", "[白眼]": "🙄", "[嘘]": "🤫",
            "[衰]": "😰", "[委屈]": "😣", "[吐]": "🤮", "[哈欠]": "😴", "[抱抱]": "🤗", "[怒]": "😡", "[疑问]": "❓", "[拜拜]": "👋",
            "[思考]": "🤔", "[汗]": "😓", "[困]": "😴", "[睡]": "😴", "[钱]": "🤑", "[失望]": "😔", "[酷]": "😎", "[色]": "😍",
            "[哼]": "😤", "[左哼哼]": "😤", "[右哼哼]": "😤", "[鼓掌]": "👏", "[悲伤]": "😭", "[晕]": "😵", "[傻眼]": "🤪",
            "[抓狂]": "😫", "[黑线]": "😅", "[阴险]": "😏", "[怒骂]": "😡", "[心]": "❤️", "[伤心]": "💔", "[猪头]": "🐷",
            "[熊猫]": "🐼", "[兔子]": "🐰", "[ok]": "👌", "[耶]": "✌️",
            "[good]": "👍", "[NO]": "🖐", "[赞]": "👍", "[弱]": "👎", "[囧]": "😰", "[浮云]": "☁️", "[doge]": "🌚",
            "[喵喵]": "🐱", "[哆啦A梦吃惊]": "🙀", "[哆啦A梦微笑]": "😺", "[哆啦A梦花心]": "😻", "[二哈]": "🐶",
            "[书呆子]": "🤓", "[哈哈]": "😆", "[太阳]": "🌞", "[月亮]": "🌛", "[跪了]": "🤪", "[费解]": "🤔", "[挖鼻]": "🌝",
            "[允悲]": "🤦‍♂️", "[围观]": "👀", "[摊手]": "🤷🏻‍♂️", "[话筒]": "🎤", "[打脸]": "🤪", "[笑而不语]": "🤓", "[吃瓜]": "🍉",
            "[憧憬]": "🤩", "[并不简单]": "🧐", "[蜡烛]": "🕯️", "[拳头]": "✊", "[加油]": "💪", "[笑cry]": "😂", "[馋嘴]": "😋",
            "[可怜]": "😿", "[蛋糕]": "🍰", "[顶]": "😆", "[握手]": "🤝"
        }
        for k, v in emoji_map.items():
            result_text = result_text.replace(k, v)
        result_text = re.sub(re.compile(r'\[.{1,5}\]'), ' ', result_text)  # 将其余可能无法转换的表情删掉
        result_text = re.sub(re.compile(r"\s*\.?\s*\u200b*$"), "", result_text)  # 去掉文本末尾的点
        result_text = re.sub(re.compile(r"全文$"), "...", result_text)  # 将尾部全文替换为...
        return [result_text.strip()]

    @staticmethod
    def parse_raw_blog(raw_blog):
        """把raw的一条微博转化为需要的格式"""
        blog = {
            "created_at": raw_blog.get("created_at", ""),
            "id": raw_blog.get("id", None),
            "text": WeiboAPI.weibo_text(raw_blog.get("text", "")),
            "source": raw_blog.get("source", ""),
            "author": WeiboAPI.parse_user_info(raw_blog.get("user", {}))
        }
        if raw_blog.get("pic_num", 0) > 0 and "pics" in raw_blog:
            pics = []
            raw_pics = raw_blog.get("pics", [])
            for raw_pic in raw_pics:
                pic = {
                    "pid": raw_pic["pid"],
                    "url": raw_pic["url"]
                }
                if "large" in raw_pic:
                    pic["large_url"] = raw_pic["large"]["url"]
                pics.append(pic)
            blog["pic_num"] = raw_blog["pic_num"]
            blog["pics"] = pics
        return blog

    @staticmethod
    def parse_user_info(user_info_raw):
        """把raw的一个用户信息转化为需要的格式"""
        return {
            "uid": user_info_raw.get("id", None),
            "screen_name": user_info_raw.get("screen_name", ""),
            "profile_image_url": user_info_raw.get("profile_image_url", ""),
            "gender": user_info_raw.get("gender", None)
        }

    @classmethod
    def get_user_info(cls, uid, raw=False):
        """获取用户基础信息"""

        uid = '%d' % float(uid)
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return []

        params = {
            'containerid': '100505{}'.format(uid),
            'type': 'uid',
            'value': uid
        }
        r = requests.get(cls.BASE_URL, params=params, cookies=cookies, timeout=3)
        Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)

        raw_result = r.json()

        if raw_result["ok"] is 0:
            raise RequestException(raw_result['msg'])
        else:
            if raw:
                return raw_result
            else:
                user_info_raw = raw_result["data"]["userInfo"]
                user_info = WeiboAPI.parse_user_info(user_info_raw)
                return user_info

    @classmethod
    def get_user_following(cls, uid):
        """Ta关注的人"""

        uid = '%d' % float(uid)
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return []

        params = {
            'luicode': '10000011',
            'lfid': '100505{}'.format(uid),
            'containerid': '231051_-_followers_-_{}'.format(uid),
            'featurecode': '20000320',
            'type': 'uid',
            'value': uid
        }
        followed_id_list = []
        for page_id in range(1, 5):
            params['page'] = page_id
            r = requests.get(cls.BASE_URL, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                if raw_result['data'].get('cards'):
                    for card in raw_result['data']['cards']:
                        for u in card['card_group']:
                            if u['card_type'] == 10:
                                followed_id_list.append(u["user"]["id"])
        return followed_id_list

    @classmethod
    def get_user_blogs(cls, uid, raw=False):
        """Ta发的微博"""

        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        params = {
            'type': uid,
            'value': uid,
            'containerid': '107603{}'.format(uid),
            'uid': uid
        }

        blogs = []
        for page_id in range(1, 5):
            params['page'] = page_id
            r = requests.get(cls.BASE_URL, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                if raw:
                    blogs.append(raw_result)
                else:
                    for item in raw_result["data"]["cards"]:
                        if item["card_type"] == 9:
                            raw_blog = item["mblog"]
                            blog = WeiboAPI.parse_raw_blog(raw_blog)
                            blogs.append(blog)
        return blogs

    @classmethod
    def get_user_likes(cls, uid, raw=False):
        """Ta赞过的微博"""
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        params = {
            'containerid': '230869{}_-_mix'.format(uid)
        }

        blogs = []
        for page_id in range(1, 5):
            params['page'] = page_id
            r = requests.get(cls.BASE_URL, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                if raw:
                    blogs.append(raw_result)
                else:
                    for item in raw_result["data"]["cards"]:
                        if item["card_type"] == 9:
                            raw_blog = item["mblog"]
                            blog = WeiboAPI.parse_raw_blog(raw_blog)
                            blogs.append(blog)
                        if item["card_type"] == 11:
                            for card in item["card_group"]:
                                if card["card_type"] == 9:
                                    raw_blog = card["mblog"]
                                    blog = WeiboAPI.parse_raw_blog(raw_blog)
                                    blogs.append(blog)
        return blogs

    @classmethod
    def get_blog_detail(cls, weibo_id, raw=False):
        """
        获得一条微博详细信息。
        :param raw: 是否返回raw data
        :param weibo_id: 微博id
        """
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        url = 'https://m.weibo.cn/statuses/show?id={}'.format(weibo_id)
        r = requests.get(url, cookies=cookies, timeout=3)
        Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
        raw_result = r.json()

        if raw_result["ok"] is 0:
            raise RequestException(raw_result['msg'])
        else:
            if raw:
                return raw_result
            else:
                raw_blog = raw_result["data"]
                blog = WeiboAPI.parse_raw_blog(raw_blog)
                return blog

    @classmethod
    def get_blog_comments(cls, weibo_id, raw=False):
        """
        获得一条微博下的评论。
        分页接口，一次只拿20个。
        :param weibo_id: 微博的id
        :param raw: 是否返回raw data
        """
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        params = {
            'id': weibo_id,
            'mid': weibo_id
        }
        url = 'https://m.weibo.cn/comments/hotflow'

        comments = []
        for _ in range(1, 5):
            r = requests.get(url, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                raw_data = raw_result["data"]
                params['max_id'] = raw_data["max_id"]
                params['max_id_type'] = raw_data['max_id_type']
                if raw:
                    comments += raw_data['data']
                else:
                    for c in raw_data['data']:
                        comments.append(WeiboAPI.parse_raw_blog(c))

        return comments

    @classmethod
    def get_blog_likes(cls, weibo_id, raw=False):
        """获得一条微博下的点赞"""
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        params = {
            'id': weibo_id
        }
        url = 'https://m.weibo.cn/api/attitudes/show'

        likes = []
        for page_id in range(1, 5):
            params['page'] = page_id
            r = requests.get(url, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                raw_data = raw_result["data"]
                if raw:
                    likes += raw_data['data']
                else:
                    for l in raw_data['data']:
                        likes.append(WeiboAPI.parse_raw_blog(l))
        return likes

    @classmethod
    def get_blog_reposts(cls, weibo_id, raw=False):
        """获得一条微博的转发"""
        db = DB.get_crawlerdb()
        cookies_id, cookies = Cookies.get_cookies(cls.cookies_policies, cls.cookies_type, db)
        if not cookies:
            return None

        params = {
            'id': weibo_id
        }
        url = 'https://m.weibo.cn/api/statuses/repostTimeline'

        reposts = []
        for page_id in range(1, 5):
            params['page'] = page_id
            r = requests.get(url, params=params, cookies=cookies, timeout=3)
            Cookies.update_cookies(cookies_id, cls.cookies_type, r, db)
            raw_result = r.json()

            if raw_result["ok"] is 0:
                raise RequestException(raw_result['msg'])
            else:
                raw_data = raw_result["data"]
                if raw:
                    reposts += raw_data['data']
                else:
                    for l in raw_data['data']:
                        reposts.append(WeiboAPI.parse_raw_blog(l))

        return reposts
