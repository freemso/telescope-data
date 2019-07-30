import json
import logging
import time
from functools import wraps, partial

from flask import Flask, Response, request
from flask_cors import CORS
from requests import RequestException

from api.douban import DoubanAPI
from api.weibo import WeiboAPI

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


@app.route('/douban/user/info', methods=['GET'])
@api_wrapper
def douban_user_info():
    data = request.values
    uid = data['uid']
    raw = data.get("raw", False)
    if uid:
        try:
            result = DoubanAPI.get_user_info(uid)
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
