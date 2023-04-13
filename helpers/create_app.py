import pathlib

from quart import Quart, Blueprint
from quart_cors import cors

import config
import storage.integrated
from utils.logger import logger


class Backend(Quart):
    def __init__(self, config_instance: object = None, blueprints: list[Blueprint] | tuple[Blueprint] = None):
        from blueprints import root_bp, file_bp

        super().__init__(__name__, instance_relative_config=True,
                         instance_path=str(pathlib.Path('instance').absolute()))
        if config_instance:
            self.config.from_object(config_instance)

        self.register_blueprint(root_bp)
        self.register_blueprint(file_bp)

        if blueprints:  # pragma: no cover
            for blueprint in blueprints:
                self.register_blueprint(blueprint)

        logger.success(f"iAirShare {config_instance.BACKEND_Name} "
                       f"{config_instance.SERVER_VersionCode}({config_instance.SERVER_Version})")
        logger.success(f"Running on {config_instance.HOST}:{config_instance.PORT} "
                       f"DEBUG: {config_instance.DEBUG}")


def create_app():
    if hasattr(config, "APP_APP") and config.APP_APP:
        app = config.APP_APP
    elif hasattr(storage.integrated, "app") and storage.integrated.shared.app:
        app = storage.integrated.shared.app
    else:
        app = Backend(config_instance=config)

    cors(
        app,
        allow_methods=['GET', 'PUT', 'DELETE', 'POST']
    )

    storage.integrated.setup_db_app(app)
    config.APP_APP = app

    return app