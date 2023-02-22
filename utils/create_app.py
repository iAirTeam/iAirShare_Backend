import pathlib

from flask import Flask
from flask_cors import CORS

import config
from blueprints import file_bp, root_bp


def create_app():
    app = Flask(__name__, instance_relative_config=True,
                instance_path=str(pathlib.Path('instance').absolute()))

    app.config.from_object(config)

    CORS(app, methods=['GET', 'PUT', 'DEL', 'POST'],
         supports_credentials=True)

    config.SQLALCHEMY_INSTANCE.init_app(app)

    app.register_blueprint(file_bp)
    app.register_blueprint(root_bp)

    return app
