import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen, logger
from utils.files import FileAPIPublic
from http import HTTPStatus

bp = Blueprint("file", __name__, url_prefix='/api/file')
public_repo = FileAPIPublic()


def file_iter(count, path, d_next):
    if count > 20:
        count = 20
    first, total, d_next = public_repo.next_repo_dir(path, d_next=d_next)
    result = {"total": total, 'next': 0, 'list': [first]}

    for _ in range(count):
        if d_next == 0:
            break

        val, total, d_next = public_repo.next_repo_dir(None, d_next=d_next)

        if val is None:
            break
        result['total'] = total
        result['list'].append(val)

    result['next'] = d_next

    return result


@bp.route('/list_root', methods=['GET', 'POST'])
def get_file_list():
    count = request.values.get('count', 0)
    d_next = request.values.get('next', 0)
    try:
        count = int(count)
        d_next = int(d_next)
    except ValueError:
        return kw_gen(code=400, msg='bad argument')
    result = file_iter(count, '/', d_next)

    return kw_gen(code=200, data=result)


# noinspection PyProtectedMember
@bp.route('/<repo>', methods=['GET', 'PUT', 'POST'])
def files_operation(repo='public'):
    if repo != 'public':
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(code=400, msg='bad argument')

            if not filename:
                result = file_iter(count, '/', d_next)

                return kw_gen(code=200, data=result)
            else:
                # TODO: Get File here, but not now!
                return kw_gen(code=400, msg="I don't want to make it work! :(")

        case "PUT" | "POST":
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, code=400)

            result = []

            for file in files:
                file_hash, path = public_repo.upload_repo_file("/", file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)


# noinspection PyProtectedMember
@bp.route('/<repo>/<path:_>', methods=['GET', 'PUT', 'DELETE'])
def file_operation(repo='public', _=None):
    storage_path = request.full_path.lstrip(f'file/{repo}') \
        .rstrip('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args)))

    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid Storage Path")

    if repo != 'public':
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case 'GET':
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            try:
                count = int(count)
                d_next = int(d_next)
            except ValueError:
                return kw_gen(code=400, msg='bad argument')

            file_id = public_repo.quires_repo_file(storage_path)

            if not file_id:
                return kw_gen(code=404, msg='file not found')

            if file_id == '[Directory]':
                result = file_iter(count, storage_path, d_next)

                return kw_gen(code=200, data=result)

            return send_file(public_repo._queries(file_id),
                             mimetype='file')
        case 'PUT' | 'POST':
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, code=400)

            result = []

            for file in files:
                file_hash, path = public_repo.upload_repo_file(storage_path, file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)
        case 'DELETE':
            if not storage_path.lstrip('/'):
                return kw_gen(_status=HTTPStatus.GONE,
                              data=hash(public_repo.unlink_repo_file(storage_path)))
            else:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST,
                              code=400)
