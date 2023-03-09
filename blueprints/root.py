from flask import Blueprint, send_file, url_for

from utils import gen_json_response

from config import SERVER_NAME

bp = Blueprint("root", __name__)


@bp.route('/')
def index():
    return gen_json_response({
        "name": SERVER_NAME,
        "versionCode": 'alpha',
        "version": -3,
    })


@bp.route('/robots.txt')
def robots():
    return send_file('')
