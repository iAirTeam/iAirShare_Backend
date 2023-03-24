from quart import Blueprint, send_file, websocket

from utils import gen_json_response

from config import BACKEND_Name, SERVER_Version, SERVER_VersionCode

bp = Blueprint("ws_file_api", __name__)


@bp.websocket("/test")
async def test_ws():
    return await websocket.send_json(await websocket.receive_json())
