import pathlib

from quart import Quart
from quart_cors import cors

import config
import storage.integrated
from blueprints import *


def create_app():
    app = Quart(__name__, instance_relative_config=True,
                instance_path=str(pathlib.Path('instance').absolute()))

    app.config.from_object(config)

    cors(app,
         allow_methods=['GET', 'PUT', 'DELETE', 'POST']
         )

    app.register_blueprint(file_bp)
    app.register_blueprint(root_bp)

    storage.integrated.setup_db_app(app)
    config.APP_APP = app

    return app
