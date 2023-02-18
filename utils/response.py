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
    _dict = deepcopy(default_response)
    _dict.update(kwargs)
    return json.dumps(_dict, ensure_ascii=False, indent=4)


def gen_json_response_kw(_status=HTTPStatus.OK, **kwargs) -> Response:
    return Response(gen_response_str(**kwargs),
                    mimetype='application/json', status=_status)


def gen_json_response(dictionary: dict, _status=HTTPStatus.OK) -> Response:
    return Response(json.dumps(dictionary, ensure_ascii=False),
                    mimetype='application/json', status=_status)
