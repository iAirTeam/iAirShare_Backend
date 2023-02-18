from os.path import abspath

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from blueprints import file_bp, root_bp
import config


def create_app():
    app = Flask(__name__, instance_relative_config=True, instance_path=abspath('instance'))

    app.config.from_object(config)

    CORS(app, methods=['GET', 'PUT', 'DEL', 'POST'], supports_credentials=True)
    # SQLAlchemy(app)

    app.register_blueprint(file_bp)
    app.register_blueprint(root_bp)

    return app
