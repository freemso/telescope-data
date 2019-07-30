import logging

from pymongo import UpdateOne

from utils.db import DB


class HistoryCrawler:
    """返回历史池子中的爬虫消息"""
    logger = logging.getLogger(__name__)

    @classmethod
    def get_items(cls, crawler_type, account, limit=2):
        try:
            mongo_db = DB.get_crawlerdb()
            items = []
            operations = []
            for item in mongo_db.historyitems.find({'type': crawler_type, 'account': account, 'used': {'$ne': True}}).limit(limit):
                operations.append(UpdateOne({'_id': item['_id']}, {
                    '$set': {'used': True},
                    '$currentDate': {
                        'usedAt': True}
                }))
                del item['_id']
                items.append(item)
            if operations:
                mongo_db.historyitems.bulk_write(operations)
            return items
        except Exception:
            cls.logger.exception('get_items error.')
            return None
