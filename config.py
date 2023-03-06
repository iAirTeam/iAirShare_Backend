from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

import storage.shared as shared

HOST = "0.0.0.0"
PORT = 10000
DEBUG = True
SECRET_KEY = "AS830648803044"
PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SQLALCHEMY_DATABASE_URI = 'sqlite://'
ADMIN_CODE = '123456'

shared.SECRET_KEY = SECRET_KEY

APP_SQLALCHEMY_INSTANCE = shared.sqlalchemy
if 'app' in shared.__dict__:
    APP_APP: Flask = shared.app
