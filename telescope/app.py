import json
import logging
import time
from functools import wraps, partial

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from requests import RequestException

from api.bilibili import Bilibili
from api.douban import DoubanAPI
from api.historycrawler import HistoryCrawler
from api.weibo import WeiboAPI
from api.xiaohongshu import XiaoHongShuApi
from api.zhihu import ZhihuAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(module)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, supports_credentials=True)


def _is_ok(value):
    return (value is not None) and (value is not False)


def _error_resp(err):
    return Response(json.dumps({"ok": False, "error": err, "result": None}), mimetype='application/json')


def _ok_resp(result):
    return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')


PARAMS_ERROR_RESP = _error_resp("Invalid parameter.")


def api_wrapper(f=None, *, err_resp=None):
    if f is None:
        return partial(api_wrapper, err_resp=err_resp)
    if err_resp is None:
        err_resp = Response('{"ok": false, "error": "some internal error.", "result": []}', mimetype='application/json')

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            start = time.time()
            resp = f(*args, **kwargs)
            cost = (time.time() - start) * 1000
            logging.info('%s cost %.3f millseconds', f.__name__, cost)
            return resp
        except Exception:
            logging.exception('%s failed.', f.__name__)
            return err_resp
    return decorated_function


@app.route('/hz')
@api_wrapper
def is_alive():
    """
    存活确认。
    """
    return 'well'


@app.route("/weibo/user/info", methods=["GET"])
@api_wrapper
def weibo_user_info():
    data = request.values
    uid = data['uid']
    raw = data.get("raw", False)
    if uid:
        try:
            result = WeiboAPI.get_user_info(uid, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route("/weibo/user/following", methods=["GET"])
@api_wrapper
def weibo_user_following():
    data = request.values
    uid = data['uid']
    if uid:
        try:
            result = WeiboAPI.get_user_following(uid)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/user/blogs', methods=['GET'])
@api_wrapper
def weibo_user_blogs():
    data = request.values
    uid = data['uid']
    raw = data.get("raw", False)
    if uid:
        try:
            result = WeiboAPI.get_user_blogs(uid, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/user/likes', methods=['GET'])
@api_wrapper
def weibo_user_likes():
    data = request.values
    uid = data['uid']
    raw = data.get("raw", False)
    if uid:
        try:
            result = WeiboAPI.get_user_likes(uid, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/blog/detail', methods=['GET'])
@api_wrapper
def weibo_blog_detail():
    data = request.values
    weibo_id = data['id']
    raw = data.get("raw", False)
    if weibo_id:
        try:
            result = WeiboAPI.get_blog_detail(weibo_id, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/blog/comments', methods=['GET'])
@api_wrapper
def weibo_blog_comments():
    data = request.values
    weibo_id = data['id']
    raw = data.get("raw", False)
    if weibo_id:
        try:
            result = WeiboAPI.get_blog_comments(weibo_id, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/blog/likes', methods=['GET'])
@api_wrapper
def weibo_blog_likes():
    data = request.values
    weibo_id = data['id']
    raw = data.get("raw", False)
    if weibo_id:
        try:
            result = WeiboAPI.get_blog_likes(weibo_id, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/weibo/blog/reposts', methods=['GET'])
@api_wrapper
def weibo_blog_reposts():
    data = request.values
    weibo_id = data['id']
    raw = data.get("raw", False)
    if weibo_id:
        try:
            result = WeiboAPI.get_blog_reposts(weibo_id, raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


@app.route('/douban/user/life', methods=['GET'])
@api_wrapper
def douban_user_life():
    data = request.values
    uid = data['uid']
    raw = data.get("raw", False)
    if uid:
        try:
            result = DoubanAPI.get_life_stream(uid, raw=raw)
            return _ok_resp(result)
        except RequestException as e:
            return _error_resp(e)
    return PARAMS_ERROR_RESP


# 历史遗留


@app.route('/api/bilibili/cate/search', methods=['GET'])
@api_wrapper
def api_bilibili_cate_search():
    cate_id = request.args.get('cateId')
    head_size = request.args.get('headSize')
    min_play = request.args.get('minPlay')

    head_size = None if head_size == '' or head_size is None else int(head_size)
    min_play = None if min_play == '' or min_play is None else int(min_play)
    if cate_id and (head_size is not None or min_play is not None):
        result = Bilibili.cate_search_hot_rank(cate_id, head_size=head_size, min_play=min_play, limit=int(request.args.get('limit', 10)))
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/openapi/bilibili/member/getSubmitVideos', methods=['GET'])
@app.route('/api/bilibili/member/getSubmitVideos', methods=['GET'])
@api_wrapper
def api_bilibili_submit_videos():
    mid = request.args.get('mid')
    page = request.args.get('page', 1)
    if mid:
        result = Bilibili.get_submit_videos(mid, page)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/openapi/bilibili/search', methods=['GET'])
@app.route('/api/bilibili/search', methods=['GET'])
@api_wrapper
def api_bilibili_search():
    keywords = request.args.get('keywords')
    page = request.args.get('page', '1')
    if keywords and page:
        result = Bilibili.search(keywords, page)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/api/zhihu/exploreAnswer', methods=['POST', 'GET'])
@api_wrapper
def api_zhihu_explore_answer():
    topics = request.args.get('topics')
    if topics:
        result = ZhihuAPI.explore_answer(topics)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/api/zhihu/getMoments', methods=['GET'])
@api_wrapper
def api_zhihu_get_moments_by_id():
    user_id = request.args.get('id')
    if user_id:
        result = ZhihuAPI.get_monments_by_id(user_id)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/api/xiaohongshu/get_note', methods=['GET'])
@api_wrapper
def api_xiaohongshu_get_note():
    url = request.args.get('url')
    if url:
        result = XiaoHongShuApi.get_note(url)
        return Response(json.dumps({"ok": _is_ok(result), "pageJson": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/openapi/xiaohongshu/searchNotes', methods=['GET'])
@app.route('/api/xiaohongshu/searchNotes', methods=['GET'])
@api_wrapper
def api_xiaohongshu_search_notes():
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        result = XiaoHongShuApi.search_notes(keyword)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/openapi/xiaohongshu/getUserNotes', methods=['GET'])
@app.route('/api/xiaohongshu/getUserNotes', methods=['GET'])
@api_wrapper
def api_xiaohongshu_get_user_notes():
    userid = request.args.get('userid', '').strip()
    if userid:
        result = XiaoHongShuApi.get_user_notes(userid)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/openapi/xiaohongshu/getTopicNotes', methods=['GET'])
@app.route('/api/xiaohongshu/getTopicNotes', methods=['GET'])
@api_wrapper
def api_xiaohongshu_get_topic_notes():
    topicid = request.args.get('topicid', '').strip()
    filter_note_type = request.args.get('filter_note_type', 'all').strip()
    page = request.args.get('page', '1').strip()
    if topicid and filter_note_type and page:
        result = XiaoHongShuApi.get_topic_notes(topicid, filter_note_type, page)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/api/xiaohongshu/getUserProfile', methods=['GET'])
@api_wrapper
def api_xiaohongshu_get_user_profile():
    userid = request.args.get('userid', '').strip()
    if userid:
        result = XiaoHongShuApi.get_user_profile(userid)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP


@app.route('/api/xiaohongshu/shield/get', methods=['GET'])
@api_wrapper
def api_xiaohongshu_get_shield():
    count = request.args.get('count', '50').strip()
    result = XiaoHongShuApi.get_shield(count)
    return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')


@app.route('/api/xiaohongshu/shield/upload', methods=['POST'])
@api_wrapper
def api_xiaohongshu_upload_shield():
    data = request.json.get('doneStr')
    if data:
        result = XiaoHongShuApi.upload_shield(data)
        return Response(json.dumps({"ok": _is_ok(result), "result": result}), mimetype='application/json')
    return PARAMS_ERROR_RESP



@app.route('/api/history/items', methods=['GET'])
@api_wrapper
def api_history_items():
    account = request.args.get('account', '').strip()
    crawler_type = request.args.get('crawlerType', '').strip()
    count = int(request.args.get('count', 2))
    if account and crawler_type and count:
        result = HistoryCrawler.get_items(crawler_type, account, count)
        return jsonify({"ok": _is_ok(result), "result": result})
    return PARAMS_ERROR_RESP
