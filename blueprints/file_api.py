import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen, logger
from utils.files import FileAPIPublic, FileAPIPrivate
from http import HTTPStatus

bp = Blueprint("file", __name__, url_prefix='/api/file')
public_repo = FileAPIPublic()


def file_iter(req_repo, count: int, path: str, d_next):
    if count > 20:
        count = 20
    first, total, d_next = req_repo.next_repo_dir(path, d_next=d_next)
    result = {"total": total, 'next': 0, 'files': first}

    for _ in range(count):
        if d_next == 0:
            break

        val, total, d_next = req_repo.next_repo_dir(None, d_next=d_next)

        if val is None:
            break
        result['total'] = total
        result['files'].update(val)

    result['next'] = d_next

    return result


@bp.route('/<repo>/list_root', methods=['GET', 'POST'])
def get_file_list(repo='public'):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400, message='repo not exist or access denied')

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
@bp.route('/<repo>', methods=['GET', 'PUT', 'POST'])
def files_operation(repo='public'):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400, message='repo not exist or access denied')

    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, message='bad argument')

            if not filename:
                result = file_iter(req_repo, count, '/', d_next)

                return kw_gen(status=200, data=result)
            else:
                # TODO: Get File here, but not now!
                return kw_gen(status=400, message="I don't want to make it work! :(")

        case "PUT" | "POST":
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400)

            result = []

            for file in files:
                file_hash, path = req_repo.upload_repo_file("/", file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)


# noinspection PyProtectedMember
@bp.route('/<repo>/<path:fn>', methods=['GET', 'PUT', 'DELETE'])
def file_operation(repo='public', fn=None):
    req_repo = public_repo
    if repo != 'public':
        token = request.values.get('token', '')
        req_repo = FileAPIPrivate(repo, token)
        if not (req_repo.repo_exist and req_repo.can_access_repo(token)):
            return kw_gen(status=400, message='repo not exist or access denied')

    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}/') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, message="Invalid Storage Path")

    match request.method:
        case 'GET':
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(status=400, message='bad argument')

            file_id = req_repo.quires_repo_file(storage_path)

            if not file_id:
                return kw_gen(status=404, message='file not found')

            if file_id == '[Directory]':
                result = file_iter(req_repo, count, storage_path, d_next)

                return kw_gen(status=200, data=result)

            return send_file(req_repo._queries(file_id),
                             mimetype='file')
        case 'PUT' | 'POST':
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, status=400)

            result = []

            for file in files:
                file_hash, path = req_repo.upload_repo_file(storage_path, file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)
        case 'DELETE':
            if not storage_path.lstrip('/'):
                return kw_gen(_status=HTTPStatus.GONE,
                              data=hash(req_repo.unlink_repo_file(storage_path)))
            else:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST,
                              status=400)
