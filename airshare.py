import os
import re
import copy
from typing import Optional

from flask import Response, jsonify

import json

from config import config

from enum import Enum

from http import HTTPStatus

default_response = {
    "code": 200,
    "msg": "success",
    "data": None
}


class AvailableTypes(Enum):
    Available = 0
    Unavailable = 1
    Maintain = 2


service_available = AvailableTypes.Available


def gen_response_str(**kwargs) -> str:
    _dict = copy.deepcopy(default_response)
    _dict.update(kwargs)
    return json.dumps(_dict, ensure_ascii=False, indent=4)


def gen_json_response_kw(_status=HTTPStatus.OK, **kwargs) -> Response:
    return Response(gen_response_str(**kwargs),
                    mimetype='application/json', status=_status)


def gen_json_response(dictionary: dict, status=HTTPStatus.OK) -> Response:
    return Response(gen_response_str(**dictionary),
                    mimetype='application/json', status=status)


def get_file_full_path(filename) -> Optional[str]:
    path = os.path.join(os.path.abspath(config.get('files_path', "./files")), filename)
    return path if os.path.exists(path) else None


def safe_filename(filename: str):
    for sep in os.path.sep, os.path.altsep:
        if sep:
            filename = filename.replace(sep, "_")

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    nt_badnames = ("CON", "AUX", "COM1", "COM2", "COM3", "COM4", "LPT1", "LPT2", "LPT3", "PRN", "NUL")
    if (os.name == "nt"
            and filename
            and filename.split(".")[0].upper() in nt_badnames):
        filename = f"_{filename}"

    return filename
