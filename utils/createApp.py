from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath

from blueprints import api_bp
import config


def create_app():
    app = Flask(__name__, instance_relative_config=True, instance_path=abspath('instance'))

    app.config.from_object(config)

    CORS(app, methods=['GET', 'PUT', 'DEL', 'POST'], supports_credentials=True)
    SQLAlchemy(app)

    app.register_blueprint(api_bp)

    return app
