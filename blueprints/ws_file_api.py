from quart import Blueprint, send_file, websocket

from helpers import gen_formatted_dict as gen_dict

from storage import FileAPIPublic, FileAPIPrivate

from config import BACKEND_Name, SERVER_Version, SERVER_VersionCode

bp = Blueprint("ws_file_api", __name__, url_prefix='/api/ws')


@bp.websocket("/test")
async def test_ws():
    await websocket.accept()
    return await websocket.send_json(await websocket.receive_json())


@bp.websocket('/viewer')
async def viewer():
    repo_access = FileAPIPublic()

    await websocket.accept()

    while True:
        initialize_data_json: dict = await websocket.receive_json()

        repo_id = initialize_data_json.get("root", "public")

        access_token = initialize_data_json.get("token", '')

        auto_create = initialize_data_json.get("create", False)

        if repo_id != 'public':
            repo_access = FileAPIPrivate(repo_id, access_token, auto_create)
            if not repo_access.can_access:
                await websocket.send_json(gen_dict(code=400, msg="repo can be accessed"))
                continue
        break

    cur_dir = '/'

    while True:
        action_json: dict = await websocket.receive_json()

        action = action_json.get('action', None)

        if not action:
            await websocket.send_json(gen_dict(code=400, msg="Invalid action"))

        match action:
            case 'list':
                await websocket.send_json(gen_dict(data=repo_access.list_dir(cur_dir)))
            case 'download':
                filename = action_json.get('file', None)
                slice_size = action_json.get('slice', None)

                length = 0

                with repo_access.get_file(repo_access.quires_file(f'{cur_dir}{filename}').file_property) as io:
                    length = len(io.getvalue())
                    while not (io.tell() >= length):
                        await websocket.send(
                            io.read(slice_size)
                        )

                await websocket.send_json(gen_dict(code=200, msg='All bytes are sent.'))
            case 'stat':
                filename = action_json.get('file', None)

                file = repo_access.quires_file(f'{cur_dir}{filename}')

                file.pointer = None
                file.file_property['file_id'] = ''

                await websocket.send_json(gen_dict(code=200, data={
                    *file.__dict__
                }))
            case 'cd':
                filename = action_json.get('file', None)
                await websocket.close(-1, "bad action")
                raise NotImplementedError("Not Implemented now!")
            case 'quit':
                await websocket.close(0, 'user closed')
            case _:
                await websocket.send_json(gen_dict(code=400, msg='Invalid action'))
