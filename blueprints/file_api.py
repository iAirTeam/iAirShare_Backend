from http import HTTPStatus

from quart import Blueprint, request, send_file

from storage import FileAPIPublic, FileAPIPrivate, AdminFileAPI, FileType, Directory
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen
from config import logger

bp = Blueprint("file", __name__, url_prefix='/api/file')
public_repo = FileAPIPublic()


def file_iter(req_repo, count: int, path: str, d_next):
    logger.debug(f"[File Iter] Iterating (iter_id:{d_next}) at {path} in {req_repo.repo_name}")
    if count > 20:
        count = 20
    first, total, d_next = req_repo.next_repo_dir(path, d_next=d_next)
    result = {"total": total, 'next': 0, 'files': [first]}
    logger.debug(f"[File Iter] Total: {total} Element {first}")

    for _ in range(count):
        if d_next == 0:
            break

        val, total, d_next = req_repo.next_repo_dir(None, d_next=d_next)

        if val is None:
            break
        result['total'] = total
        result['files'].append(val)

    logger.debug(f"[File Iter] Iter Complete with iter_id: ({d_next})")

    result['next'] = d_next

    return result


@bp.route('/<repo>/', methods=['GET', 'PUT'])
@bp.route('/<repo>', methods=['GET', 'POST'])
async def files_operation(repo='public'):
    values = await request.values

    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    req_repo = public_repo
    if repo != 'public':
        create = bool(values.get('create', False))
        token = values.get('token', '')
        req_repo = FileAPIPrivate(repo, token, create_not_exist=create)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            logger.debug(f"Requested Repo {repo} \n"
                         f"E:{req_repo.repo_exist} A:{req_repo.can_access_repo(token)}")
            return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400,
                          msg="Requested Repo does not exist or Access Denied.")

    logger.info(f"Requested (/) in Repo {req_repo.repo_name}({repo}) with tok:{values.get('token', '')}")

    match request.method:
        case "GET":
            if not storage_path.endswith('/'):
                logger.debug(f"Fetch Repo Info for {req_repo.repo_name}({repo})")
                return dict_gen({
                    "repo_name": req_repo.repo_name
                })

            count = values.get('count', 0)
            d_next = values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                logger.debug(f"Cannot parse count:{count} next:{d_next}")
                return kw_gen(status=400, msg='Invalid count or next')

            result = file_iter(req_repo, count, '/', d_next)

            logger.debug(f"Result: len:{len(result)}")

            return kw_gen(status=200, data=result)

        case "PUT":
            if not storage_path.endswith('/'):
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                              msg="Unable to put a file to root")

            files = (await request.files).getlist('file')

            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                              msg="No File Selected")

            for file in files:
                await req_repo.upload_repo_file("/", file)

            return kw_gen(_status=HTTPStatus.CREATED)

        case 'DELETE':
            if not isinstance(req_repo, FileAPIPublic):
                req_repo.config_dir.unlink()
                return kw_gen(_status=HTTPStatus.RESET_CONTENT, status=200)
        case 'POST':
            action = (await request.values).get('action')
            match action:
                case 'save':
                    req_repo.save_storage()
                case 'reload':
                    ...
                case 'create':
                    ...
            return kw_gen(_status=HTTPStatus.OK, msg='Success')


@bp.route('/<repo>/<path:_>', methods=['GET', 'PUT', 'DELETE'])
async def file_operation(repo='public', _=None):
    values = await request.values

    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}/') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    req_repo = public_repo
    if repo == 'admin':
        token = values.get('token', '')
        path_list = storage_path.removesuffix('/').split('/')

        access_repo = path_list[0]

        new_storage_path = '/' + '/'.join(path_list[1:]) + \
                           ('/' if storage_path.endswith('/') else '')

        req_repo = AdminFileAPI(repo_id=access_repo, token=token)

        repo = access_repo
        storage_path = new_storage_path

        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400,
                          msg="Requested Repo Access Denied or repo does not Exist")
    elif repo != 'public':
        token = values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            logger.debug(f"Requested Repo {repo} \n"
                         f"E:{req_repo.repo_exist} A:{req_repo.can_access_repo(token)}")
            return kw_gen(status=400,
                          msg="Requested Repo does not Exist or Access Denied")

    logger.info(
        f"Requested ({storage_path}) in Repo {req_repo.repo_name}({repo}) with tok:{values.get('token', '')}")

    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid Storage Path")

    match request.method:
        case 'GET':
            file_info = req_repo.quires_repo_file(storage_path)

            if not file_info:
                return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400,
                              msg='Unable to locate file')

            is_dir = storage_path.endswith('/')

            logger.debug(f"Requested {file_info} at {storage_path} "
                         f"req is_dir:{is_dir}")

            if not is_dir:
                if file_info.file_type != FileType.file:
                    return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                                  msg="Invalid located file type")

                file_info = req_repo.locate_file(storage_path)

                return await send_file(
                    req_repo.get_file_path(file_info.file_property),
                    attachment_filename=file_info.file_name,
                    last_modified=file_info.file_property['last_update'],
                )

            count = values.get('count', 0)
            d_next = values.get('next', 0)

            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, msg='Invalid count or next')

            if file_info.file_type == FileType.directory:
                result = file_iter(req_repo, count, storage_path, d_next)

                return kw_gen(status=200, data=result)
        case 'PUT':
            files = (await request.files).getlist('file')

            if not storage_path.endswith('/'):
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, code=400,
                              msg="Unable to put File(s) into a FILE")

            if files:
                if len(files) == 0:
                    return kw_gen(_status=HTTPStatus.ACCEPTED, code=202,
                                  msg="Notice: No File Selected!")
                for file in files:
                    await req_repo.upload_repo_file(storage_path, file)

                return kw_gen(_status=HTTPStatus.CREATED)

            path_list = storage_path.strip('/').split('/')
            return kw_gen(
                _status=HTTPStatus.CREATED,
                place=req_repo.set_file(
                    '/'.join(path_list[:-1]),
                    Directory(
                        file_name=path_list[-1],
                        pointer=set()
                    )
                )
            )
        case 'DELETE':
            if not storage_path.removesuffix('/'):
                return kw_gen(_status=HTTPStatus.GONE,
                              data=hash(req_repo.unlink_repo_file(storage_path)))
            else:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST,
                              status=400)
