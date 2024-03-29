import datetime
import json
from copy import deepcopy
from http import HTTPStatus

from quart import Response

default_response = {
    "status": 200,
    "msg": "",
    "data": None
}


def _serialize(obj):
    if isinstance(obj, datetime.datetime):
        return obj.timestamp()
    else:
        return obj.__dict__


def gen_response_str(**kwargs) -> str:
    """
    使用模板生成 json 响应字符串
    :param kwargs:
    :return: json 响应字符串
    """
    _dict = get_formatted_dict(kwargs)
    return json.dumps(_dict, ensure_ascii=False, default=_serialize)


def gen_json_response_kw(_status=HTTPStatus.OK, _cache_timeout: int = None, **kwargs) \
        -> Response:
    """
    根据 keyword argument 生成模板 json 响应
    :param _cache_timeout: Response Cached time
    :param _status: HTTPStatus
    :param kwargs:
    :return: 响应
    """

    resp = Response(gen_response_str(**kwargs),
                    mimetype='application/json', status=_status)
    if _cache_timeout:
        resp.cache_control.max_age = _cache_timeout
        resp.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=_cache_timeout)
    return resp


def gen_json_response(dictionary: dict, _status=HTTPStatus.OK, _cache_timeout: int = None) -> Response:
    """
    通过 dict 生成 json 响应
    :param _cache_timeout: Response Cached time
    :param dictionary: 字典数据
    :param _status: HTTPStatus
    :return: 响应
    """
    resp = Response(json.dumps(dictionary, ensure_ascii=False),
                    mimetype='application/json', status=_status)
    if _cache_timeout:
        resp.cache_control.max_age = _cache_timeout
        resp.expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=_cache_timeout)
    return resp


def get_formatted_dict(dictionary: dict) -> dict:
    _dict = deepcopy(default_response)
    _dict.update(dictionary)

    return _dict


def gen_formatted_dict(**kwargs) -> dict:
    return get_formatted_dict(kwargs)
