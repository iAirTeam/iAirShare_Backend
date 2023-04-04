from quart import Blueprint, send_file

from helpers import gen_json_response

from config import BACKEND_Name, SERVER_Version, SERVER_VersionCode

bp = Blueprint("root", __name__)


@bp.route('/')
def index():
    return gen_json_response({
        "name": BACKEND_Name,
        "versionCode": SERVER_VersionCode,
        "version": SERVER_Version,
    })


@bp.route('/robots.txt')
def robots():
    return send_file('')
