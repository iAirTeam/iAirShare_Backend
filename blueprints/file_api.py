import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen, logger
from storage import FileAPIPublic, FileAPIPrivate, FileType, File, Directory
from http import HTTPStatus

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


@bp.route('/<repo>/_list', methods=['GET', 'POST'])
def get_file_list(repo='public'):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(_status=404, status=400, message='repo not exist or access denied')

    count = request.values.get('count', 0)
    d_next = request.values.get('next', 0)
    try:
        count = int(count)
        d_next = int(d_next)
    except ValueError:
        return kw_gen(status=400, message='bad argument')
    result = file_iter(req_repo, count, '/', d_next)

    return kw_gen(status=200, data=result)


# noinspection PyProtectedMember
@bp.route('/<repo>/')
@bp.route('/<repo>', methods=['GET', 'PUT', 'POST'])
def files_operation(repo='public'):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg='repo not exist or access denied')

    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, msg='bad argument')

            if not filename:
                result = file_iter(req_repo, count, '/', d_next)

                return kw_gen(status=200, data=result)
            else:
                # TODO: Get File here, but not now!
                return kw_gen(_status=HTTPStatus.NOT_IMPLEMENTED, status=400,
                              msg="I don't want to make it work! :(")

        case "PUT" | "POST":
            files = request.files.getlist('file')
            file_type = request.values.get('type', FileType.file)
            filename = request.values.get('filename', None)
            if not files and request.method == 'POST':
                return dict_gen({
                    "repo_name": req_repo.repo_name
                })
            elif not files and file_type == FileType.file:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400, msg="no file selected")
            elif file_type == FileType.file and filename is not None:
                req_repo.set_file('/', Directory(file_name=filename))
                return kw_gen(_status=HTTPStatus.CREATED)

            for file in files:
                req_repo.upload_repo_file("/", file)

            return kw_gen(_status=HTTPStatus.CREATED)


# noinspection PyProtectedMember
@bp.route('/<repo>/<path:_>', methods=['GET', 'PUT', 'DELETE'])
def file_operation(repo='public', _=None):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400, msg='repo not exist or access denied')

    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}/') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid Storage Path")

    match request.method:
        case 'GET':
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, msg='bad argument')

            file_info = req_repo.quires_repo_file(storage_path)

            if not file_info:
                return kw_gen(status=404, msg='file not found')

            if file_info.file_type == FileType.directory:
                result = file_iter(req_repo, count, storage_path, d_next)

                return kw_gen(status=200, data=result)

            return send_file(
                req_repo.get_file(file_info.file_property),
                download_name=file_info.file_name,
                last_modified=file_info.file_property['last_update'],
            )
        case 'PUT' | 'POST':
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400)

            for file in files:
                req_repo.upload_repo_file(storage_path, file)

            return kw_gen(_status=HTTPStatus.CREATED)
        case 'DELETE':
            if not storage_path.lstrip('/'):
                return kw_gen(_status=HTTPStatus.GONE,
                              data=hash(req_repo.unlink_repo_file(storage_path)))
            else:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST,
                              status=400)
