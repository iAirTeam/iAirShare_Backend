from datetime import timedelta

from quart_sqlalchemy import SQLAlchemy
from quart import Quart
from loguru import logger

import storage.shared as shared

AIRSHARE_BACKEND_NAME = "AirShare"
HOST = "0.0.0.0"
PORT = 10000
DEBUG = True
SECRET_KEY = "AS830648803044"
PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SQLALCHEMY_DATABASE_URI = 'sqlite://'
ADMIN_CODE = '123456'
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024

shared.SECRET_KEY = SECRET_KEY

APP_SQLALCHEMY_INSTANCE = shared.sqlalchemy
if 'app' in shared.__dict__:
    APP_APP: Quart = shared.app
