import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen, logger
from utils.files import FileAPIPublic
from http import HTTPStatus

bp = Blueprint("api", __name__)
public_repo = FileAPIPublic()


@bp.route('/filelist', methods=['GET', 'POST'])
def get_file_list():
    try:
        return gen_json_response_kw(data=get_filelist(file_path, config.FFPROBE))
    except Exception as e:
        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, status=400, msg=str(e))


# noinspection PyProtectedMember
@bp.route('/file/<repo>', methods=['GET', 'PUT', 'POST'])
def files_operation(repo='public'):
    if repo != 'public':
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            count = request.values.get('count', 0)
            d_next = request.values.get('next', 0)
            if not filename:
                if count > 20:
                    count = 20
                first, total, d_next = public_repo.next_dir('/', d_next=d_next)
                result = {"total": total, 'next': 0, 'list': [first]}

                for _ in range(count):
                    val, total, d_next = public_repo.next_dir(None, d_next=d_next)
                    result['list'].append(val)

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
                file_hash, path = public_repo.repo_upload("/", file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)


# noinspection PyProtectedMember
@bp.route('/file/<repo>/<path:storage_path>', methods=['GET', 'PUT', 'DELETE'])
def file_operation(repo='public', storage_path='/'):
    if not storage_path:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid Storage Path")

    if repo != 'public':
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case 'GET':
            return send_file(public_repo._queries(public_repo.quires_repo(storage_path)),
                             mimetype='file')
        case 'PUT' | 'POST':
            files = request.files.getlist('file')
            if not files:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST, code=400)

            result = []

            for file in files:
                file_hash, path = public_repo.repo_upload(storage_path, file)
                result.append(path)

            return kw_gen(_status=HTTPStatus.CREATED, data=result)
        case 'DELETE':
            if not storage_path.lstrip('/'):
                return kw_gen(_status=HTTPStatus.GONE,
                              data=hash(public_repo.delete(storage_path)))
            else:
                return kw_gen(_status=HTTPStatus.BAD_REQUEST,
                              code=400)


@bp.route('/setu')
@bp.route('/loli')
def _loli():
    return dict_gen(_status=HTTPStatus.IM_A_TEAPOT,
                    dictionary={'desc': 'WTH !?', 'more_desc': "What did you think about?"})
