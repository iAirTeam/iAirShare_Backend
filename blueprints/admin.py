from http import HTTPStatus

from flask import Blueprint, request, send_file
from itsdangerous import Serializer, TimedSerializer

from storage import FileAPIPublic, FileAPIPrivate, FileType, Directory
from utils import gen_json_response_kw as kw_gen, gen_json_response as dict_gen


class AdminFileAPI(FileAPIPrivate):
    def __init__(self, repo_id: str, create_not_exist=False):
        super().__init__(create_not_exist=create_not_exist, repo_name=repo_id)

    def can_access_repo(self, access_token) -> bool:
        return True


def admin_iter(req_repo: AdminFileAPI, count: int, path: str, d_next):
    if count > 30:
        count = 30

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


bp = Blueprint("file", __name__, url_prefix='/api/admin')


# noinspection DuplicatedCode
@bp.route('/access/<repo>', methods=['GET', 'PUT', 'POST'])
@bp.route('/access/<repo>/', methods=['GET', 'PUT', 'POST'])
def admin_access(repo: str = 'public'):
    req_repo = AdminFileAPI(repo)
    if req_repo.repo_exist:
        return kw_gen(_status=HTTPStatus.NOT_FOUND, status=400, msg='repo doesnt not exist')

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
                result = admin_iter(req_repo, count, '/', d_next)

                return kw_gen(status=200, data=result)

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


# noinspection DuplicatedCode
@bp.route('/<repo>/<path:_>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def file_operation(repo='public', _=None):
    req_repo = AdminFileAPI(repo)
    if req_repo.repo_exist:
        return kw_gen(status=400, msg='repo doesnt not exist')

    storage_path = request.full_path \
        .removeprefix(f'{bp.url_prefix}/{repo}/') \
        .removesuffix('?' + '&'.join(map(lambda x: f"{x}={request.args[x]}", request.args))) \
        .removesuffix('/')

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
                result = admin_iter(req_repo, count, storage_path, d_next)

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
