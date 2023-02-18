from copy import deepcopy
from flask import Response
from http import HTTPStatus
import json

default_response = {
    "status": 200,
    "msg": "",
    "data": None
}


def gen_response_str(**kwargs) -> str:
    """
    使用模板生成 json 响应字符串
    :param kwargs:
    :return: json 响应字符串
    """
    _dict = deepcopy(default_response)
    _dict.update(kwargs)
    return json.dumps(_dict, ensure_ascii=False, indent=4)


def gen_json_response_kw(_status=HTTPStatus.OK, **kwargs) -> Response:
    """
    根据 keyword argument 生成模板 json 响应
    :param _status: HTTPStatus
    :param kwargs:
    :return: 响应
    """
    return Response(gen_response_str(**kwargs),
                    mimetype='application/json', status=_status)


def gen_json_response(dictionary: dict, _status=HTTPStatus.OK) -> Response:
    """
    通过 dict 生成 json 响应
    :param dictionary: 字典数据
    :param _status: HTTPStatus
    :return: 响应
    """
    return Response(json.dumps(dictionary, ensure_ascii=False),
                    mimetype='application/json', status=_status)
