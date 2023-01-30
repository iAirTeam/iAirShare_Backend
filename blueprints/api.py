import os

from flask import Blueprint, request, send_file
from utils import gen_json_response_kw, safe_filename, get_file_full_path, gen_json_response, get_filelist
from http import HTTPStatus

bp = Blueprint("api", __name__)


@bp.route('/filelist', methods=['GET', 'POST'])
def file_list():
    try:
        return gen_json_response_kw(data=get_filelist(file_path, config.FFPROBE))
    except Exception as e:
        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, code=400, msg=str(e))


@bp.route('/file', methods=['GET', 'PUT', 'POST'])
def files_operation():
    match request.method:
        case "GET":
            filename = request.values.get('filename', None)
            if filename is None:
                try:
                    return gen_json_response_kw(data=get_filelist(file_path, config.FFPROBE))
                except Exception as e:
                    return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, code=400, msg=str(e))
            else:
                full_filename = get_file_full_path(filename)
                if filename is not None and full_filename is not None and os.path.exists(
                        full_filename) and os.path.isfile(full_filename):
                    return send_file(full_filename, download_name=filename)
                else:
                    return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, code=404,
                                                msg=f"file {filename} not found")
        case "PUT" | "POST":
            files = request.files.getlist('file')
            if not files:
                return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, code=400, msg='no_file_selected')
            for file in files:
                if file:
                    try:
                        file.save(os.path.join(config.get('files_path', "./files"), safe_filename(file.filename)))
                    except Exception as e:
                        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, code=500,
                                                    msg="upload_exception: {}".format(e), data=str(e))
                else:
                    return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, code=401, msg="unavailable_upload_file")
            return gen_json_response_kw(_status=HTTPStatus.CREATED, msg="upload successful")


@bp.route('/file/<filename>', methods=['GET', 'DELETE'])
def file_operation(filename=None):
    if not filename:
        return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, code=400, msg="Invalid filename flag")

    match request.method:
        case 'GET':
            full_filename = get_file_full_path(filename)
            if filename is not None and os.path.exists(full_filename) and os.path.isfile(full_filename):
                return send_file(full_filename, download_name=filename)
            else:
                return gen_json_response_kw(_status=HTTPStatus.NOT_FOUND, code=404, msg=f"file {filename} not found")
        case 'DELETE':
            if filename != safe_filename(filename):
                return gen_json_response_kw(code=400, msg="bad_filename_flag", status=HTTPStatus.BAD_REQUEST)

            full_filename = get_file_full_path(filename)
            try:
                os.remove(full_filename)
                return gen_json_response_kw(_status=HTTPStatus.OK, msg="delete successful")
            except OSError as e:
                return gen_json_response_kw(code=500, msg="delete_exception: {}".format(e), data=str(e))


@bp.route('/setu')
@bp.route('/loli')
def _loli():
    return gen_json_response({'desc': 'WTH !?'}, _status=HTTPStatus.IM_A_TEAPOT)
