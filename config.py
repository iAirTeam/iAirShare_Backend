from datetime import timedelta

from flask_sqlalchemy import SQLAlchemy

import utils.var

utils.var.database = SQLAlchemy()

HOST = "0.0.0.0"
PORT = 10000
DEBUG = True
SECRET_KEY = "AS830648803044"
PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SQLALCHEMY_DATABASE_URI = 'sqlite://'
SQLALCHEMY_INSTANCE = utils.var.database
