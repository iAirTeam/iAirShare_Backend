from config import config
from file import File

from flask import Flask, request, send_file, abort, render_template, Response, redirect, url_for
from flask_cors import CORS
import json
import os

from airshare import *

file_path = config.get('file_path', './files')

file_tools = File()
app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route('/')
def index():
    return Response(json.dumps({
        "name": "AirShare",
        "status": str(service_available).split('.')[1].lower(),
        "versionCode": '1.0',
        "version": 10000,
    }, ensure_ascii=False, indent=4), mimetype='application/json')


@app.route('/api/filelist', methods=['GET', 'POST'])
def file_list_api():
    if service_available is not AvailableTypes.Available:
        return gen_json_response_kw(_status=HTTPStatus.SERVICE_UNAVAILABLE, code=503, msg="service_not_available")

    try:
        return gen_json_response_kw(data=file_tools.get_filelist(config.get('files_path', "./files"),
                                                                 config.get('ffprobe', "ffprobe"),
                                                                 use_format=True))
    except Exception as e:
        return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, code=400, msg=str(e))


@app.route('/api/get_file', methods=['GET', 'POST'])
def get_file_api():  # 错误直接返回404
    if service_available is not AvailableTypes.Available:
        return gen_json_response_kw(_status=HTTPStatus.SERVICE_UNAVAILABLE, code=503, msg="service_not_available")

    filename = request.values.get("filename", None)
    if not filename:
        abort(400, "Invalid file flag")
        return
    full_filename = get_file_full_path(filename)
    if filename is not None and os.path.exists(full_filename) and os.path.isfile(full_filename):
        return send_file(full_filename, download_name=filename)
    else:
        abort(404, f"file {filename} not found")  # 404 Not Found


@app.route('/upload', methods=['GET', 'POST'])
def upload_ui():
    if request.method == 'POST':
        return jsonify(({
                                "desc": f"New Upload API is on {url_for('upload_file_api', **request.values)}"
        }))
    if service_available is not AvailableTypes.Available:
        return gen_json_response_kw(_status=HTTPStatus.SERVICE_UNAVAILABLE, code=503, msg="service_not_available")
    return render_template("upload.html", upload_dir=config.get('files_path', './files'))


@app.route('/api/upload_file', methods=['GET', 'POST'])
def upload_file_api():
    files = request.files.getlist('file')
    if not files:
        return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, code=400, msg='no_file_selected')
    for file in files:
        if file is not None and file:  # 如果文件存在bool(file)是True
            try:
                file.save(os.path.join(config.get('files_path', "./files"), safe_filename(file.filename)))
            except Exception as e:
                return gen_json_response_kw(_status=HTTPStatus.INTERNAL_SERVER_ERROR, code=500,
                                            msg="upload_exception: {}".format(e), data=str(e))
        else:
            return gen_json_response_kw(_status=HTTPStatus.BAD_REQUEST, code=401, msg="invaild_upload_file")
    return gen_json_response_kw(_status=HTTPStatus.CREATED, msg="upload successful")


@app.route('/api/setu')
@app.route('/api/loli')
def _loli():
    return gen_json_response({'desc': 'WTH !?'}, status=HTTPStatus.IM_A_TEAPOT)


if __name__ == '__main__':
    app.run(config.get('host', "0.0.0.0"), config.get('port', 10000), config.get('debug', False))
