import logging

import requests
from lxml import etree, html


class DoubanAPI:
    logger = logging.getLogger(__name__)
    proxy_policies = {
        'max_retry_times': 1,
        'proxy_used_interval': 1,
        'type': 'm.douban.com',
        'remember_proxy': False,
        'max_waiting_seconds': 1,
    }

    @classmethod
    def get_hot_list(cls):
        def _parse_item(idx, item):
            return {
                'id' : str(idx),
                'title' : item.text,
                'link' : item.attrib['href'],
                'tag' : ''
            }

        try:
            url = 'https://www.douban.com/gallery/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            }
            r = requests.get(url, headers=headers, timeout=10)
            sel = etree.HTML(r.text, parser=html.HTMLParser(encoding = 'utf-8'))
            items = sel.xpath("//ul[@class='trend']//a")
            return [_parse_item(*i) for i in enumerate(items)]
        except Exception:
            cls.logger.exception('get_hot_list error.')
            return None
