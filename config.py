from datetime import timedelta

from quart import Quart
from loguru import logger

import storage.shared as shared

# Do not modify here

logger.debug("[Config] Loading config...")

conf = -1100
SERVER_VersionCode = 'alpha'
SERVER_Version = -1100

# End of Do not modify

BACKEND_Name = "AirShare"

HOST = "127.0.0.1"
PORT = 10000
DEBUG = True
SECRET_KEY = "AS830648803044"
PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SQLALCHEMY_DATABASE_URI = 'sqlite://'
ADMIN_CODE = '123456'
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024

# Begin of HyperCorn Configuration

bind = [f"{HOST}:{PORT}"]

# End of HyperCorn

shared.SECRET_KEY = SECRET_KEY

APP_SQLALCHEMY_INSTANCE = shared.sqlalchemy
if 'app' in shared.__dict__:
    APP_APP: Quart = shared.app

logger.debug(f"[Config] Default admin password admin@{ADMIN_CODE}")
logger.debug(f"[Config] Max Content Length {MAX_CONTENT_LENGTH}")
logger.debug(f"[Config] SECRET_KEY {SECRET_KEY}")
