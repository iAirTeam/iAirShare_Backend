from http import HTTPStatus

from flask import Blueprint, request, send_file

from storage import FileAPIPublic, FileAPIPrivate, AdminFileAPI, FileType, Directory
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen

bp = Blueprint("file", __name__, url_prefix='/api/file')
public_repo = FileAPIPublic()


def file_iter(req_repo, count: int, path: str, d_next):
    if count > 20:
        count = 20
    first, total, d_next = req_repo.next_repo_dir(path, d_next=d_next)
    result = {"total": total, 'next': 0, 'files': [first]}

    for _ in range(count):
        if d_next == 0:
            break

        val, total, d_next = req_repo.next_repo_dir(None, d_next=d_next)

        if val is None:
            break
        result['total'] = total
        result['files'].append(val)

    result['next'] = d_next

    return result


@bp.route('/<repo>/', methods=['GET', 'PUT'])
@bp.route('/<repo>', methods=['GET', 'PUT'])
def files_operation(repo='public'):
    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400,
                          msg="Requested Repo does not exist or Access Denied.")

    match request.method:
        case "GET":
            if not storage_path.endswith('/'):
                return dict_gen({
                    "repo_name": req_repo.repo_name
                })

            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, msg='Invalid count or next')

            result = file_iter(req_repo, count, '/', d_next)

            return kw_gen(status=200, data=result)

        case "PUT":
            if not storage_path.endswith('/'):
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                              msg="Unable to put a file to root")

            files = request.files.getlist('file')

            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                              msg="No File Selected")

            for file in files:
                req_repo.upload_repo_file("/", file)

            return kw_gen(_status=HTTPStatus.CREATED)

        case 'DELETE':
            if not isinstance(req_repo, FileAPIPublic):
                req_repo.config_dir.unlink()
                return kw_gen(_status=HTTPStatus.RESET_CONTENT, status=200)


@bp.route('/<repo>/<path:_>', methods=['GET', 'PUT', 'DELETE'])
def file_operation(repo='public', _=None):
    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}/') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    req_repo = public_repo
    if repo == 'admin':
        token = request.values.get('token', '')
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
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400,
                          msg="Requested Repo does not Exist or Access Denied")

    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid Storage Path")

    match request.method:
        case 'GET':
            file_info = req_repo.quires_repo_file(storage_path)

            if not file_info:
                return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400,
                              msg='Unable to locate file')

            is_dir = storage_path.endswith('/')

            if not is_dir:
                if file_info.file_type != FileType.file:
                    return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400,
                                  msg="Invalid located file type")

                file_info = req_repo.locate_file(storage_path)

                return send_file(
                    req_repo.get_file(file_info.file_property),
                    download_name=file_info.file_name,
                    last_modified=file_info.file_property['last_update'],
                )

            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)

            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, msg='Invalid count or next')

            if file_info.file_type == FileType.directory:
                result = file_iter(req_repo, count, storage_path, d_next)

                return kw_gen(status=200, data=result)
        case 'PUT':
            files = request.files.getlist('file')

            if not storage_path.endswith('/'):
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, code=400,
                              msg="Unable to put File(s) into a FILE")

            if files:
                for file in files:
                    req_repo.upload_repo_file(storage_path, file)

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
