import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen, logger
from utils.files import FileAPIPublic
from http import HTTPStatus

bp = Blueprint("auth", __name__, url_prefix='/api/auth')


@bp.route('/signin/v1')
def signin_email(email):
    return kw_gen(msg=f'test {user}')
