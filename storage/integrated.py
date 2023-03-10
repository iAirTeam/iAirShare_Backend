from quart import Quart
from quart_sqlalchemy import SQLAlchemy

import storage.shared as shared
import config


def setup_db_app(app: Quart):
    shared.app = app
    if shared.sqlalchemy is None:
        shared.sqlalchemy = SQLAlchemy(app)
    else:
        shared.sqlalchemy.init_app(app)


def set_db(sqlalchemy: SQLAlchemy):
    shared.sqlalchemy = sqlalchemy


def verify_admin_code(code: str):
    return code == config.ADMIN_CODE
