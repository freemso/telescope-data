from pymongo import MongoClient

CRAWLER_MONGO_CONN_STR = "mongodb://general:NKtNFr5DggJLPuF@172.31.52.217:27017," \
                         "172.31.60.166:27017/crawler?authSource=admin&readPreference=primaryPreferred&replicaSet" \
                         "=internal_tool_rs0&readPreferenceTags=region:bj"


class DB:
    crawler_client = None
    crawler_db = None

    @classmethod
    def get_crawlerdb(cls):
        if not cls.crawler_db:
            cls.crawler_client = MongoClient(CRAWLER_MONGO_CONN_STR, socketTimeoutMS=10000, waitQueueTimeoutMS=10000)
            cls.crawler_db = cls.crawler_client.get_database()
        return cls.crawler_db

    @classmethod
    def close(cls):
        if cls.crawler_client:
            cls.crawler_client.close()
            cls.crawler_client = None
            cls.crawler_db = None
