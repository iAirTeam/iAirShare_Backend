import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw, gen_json_response, logger
from utils.files import FileAPIPublic
from http import HTTPStatus

bp = Blueprint("api", __name__)
public_repo = FileAPIPublic()


@bp.route('/filelist', methods=['GET', 'POST'])
def file_list():
    try:
        return gen_json_response_kw(data=get_filelist(file_path, config.FFPROBE))
    except Exception as e:
        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, status=400, msg=str(e))


# noinspection PyProtectedMember
@bp.route('/file/<repo>', methods=['GET', 'PUT', 'POST'])
def files_operation(repo='public'):
    if repo != 'public':
        return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            if filename is None:
                try:
                    return gen_json_response_kw(data=public_repo.get_repo_files())
                except Exception as e:
                    raise
                    return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, status=400, msg=str(e))
            else:
                full_filename = get_file_full_path(filename)
                if filename is not None and full_filename is not None and os.path.exists(
                        full_filename) and os.path.isfile(full_filename):
                    return send_file(full_filename, download_name=filename)
                else:
                    return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, status=404,
                                                msg=f"file {filename} not found")
        case "PUT" | "POST":
            files = request.files.getlist('file')
            if not files:
                return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, status=400, msg='no_file_selected')
            for file in files:
                if file:
                    try:
                        file.save(public_repo.base_dir / public_repo._safe_filename(file.filename))
                    except Exception as e:
                        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, status=500,
                                                    msg="upload_exception: {}".format(e), data=str(e))
                else:
                    return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST,
                                                status=401, msg="unavailable_upload_file")
            return gen_json_response_kw(_status=HTTPStatus.CREATED, msg="upload successful")


# noinspection PyProtectedMember
@bp.route('/file/<repo>/<filename>', methods=['GET', 'DELETE'])
def file_operation(repo='public', filename=None):
    if not filename:
        return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, status=400, msg="Invalid filename flag")

    if repo != 'public':
        return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, status=404, msg='repo_not_exist')

    match request.method:
        case 'GET':
            file = public_repo.quires_repo(filename)
            if file:
                return send_file(file, mimetype=public_repo._filetype(filename),
                                 download_name=filename)
            else:
                return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, status=404, msg=f"could not get '{filename}'")
        case 'DELETE':
            if filename != public_repo._safe_filename(filename):
                return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, status=400, msg="bad_filename_flag")

            full_filename = public_repo._file_fullpath(filename)
            try:
                full_filename.unlink()
                return gen_json_response_kw(_status=HTTPStatus.OK, msg="delete successful")
            except FileNotFoundError as e:
                return gen_json_response_kw(status=404, msg="file_not_found: {}".format(e), data=str(e))
            except OSError as e:
                return gen_json_response_kw(status=404, msg="delete_exception: {}".format(e), data=str(e))


@bp.route('/setu')
@bp.route('/loli')
def _loli():
    return gen_json_response(_status=HTTPStatus.IM_A_TEAPOT,
                             dictionary={'desc': 'WTH !?', 'more_desc': "What did you think about?"})
