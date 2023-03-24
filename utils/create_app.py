import pathlib

from quart import Quart, Blueprint
from quart_cors import cors

import config
import storage.integrated
from blueprints import *
from .logging import logger


class Backend(Quart):
    def __init__(self, config_instance: object = None, blueprints: list[Blueprint] | tuple[Blueprint] = None):
        super().__init__(__name__, instance_relative_config=True,
                         instance_path=str(pathlib.Path('instance').absolute()))
        if config_instance:
            self.config.from_object(config_instance)

        self.register_blueprint(root_bp)
        self.register_blueprint(file_bp)

        if blueprints:
            for blueprint in blueprints:
                self.register_blueprint(blueprint)

        logger.success(f"iAirShare {config_instance.BACKEND_Name} "
                       f"{config_instance.SERVER_VersionCode}({config_instance.SERVER_Version})")
        logger.success(f"Running on {config_instance.HOST}:{config_instance.PORT} "
                       f"DEBUG: {config_instance.DEBUG}")


def create_app():
    app = Backend(config_instance=config, blueprints=[ws_file_api])

    cors(
        app,
        allow_methods=['GET', 'PUT', 'DELETE', 'POST']
    )

    storage.integrated.setup_db_app(app)
    config.APP_APP = app

    return app
