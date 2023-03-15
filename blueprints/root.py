from quart import Blueprint, send_file

from utils import gen_json_response

from config import AIRSHARE_BACKEND_NAME

bp = Blueprint("root", __name__)


@bp.route('/')
def index():
    return gen_json_response({
        "name": AIRSHARE_BACKEND_NAME,
        "versionCode": 'alpha',
        "version": -3,
    })


@bp.route('/robots.txt')
def robots():
    return send_file('')
