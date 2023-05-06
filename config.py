from datetime import timedelta

from quart import Quart
from utils.logger import logger

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
SECRET_KEY = "AS830648803044"  # Key used salted file hash & cookie storage
PERMANENT_SESSION_LIFETIME = timedelta(days=14)
SQLALCHEMY_DATABASE_URI = 'sqlite://'
ADMIN_CODE = '123456'
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024
USE_RELOADER = True

# Begin of HyperCorn Configuration

bind = [f"{HOST}:{PORT}"]
compress_min_size = 20480
use_reloader = USE_RELOADER

# End of HyperCorn

# Do not modify here

shared.SECRET_KEY = SECRET_KEY

APP_SQLALCHEMY_INSTANCE = shared.sqlalchemy
if 'app' in shared.__dict__:
    APP_APP: Quart = shared.app

logger.info(f"[Config] Admin access admin@{ADMIN_CODE}")
logger.debug(f"[Config] Max Content Length {MAX_CONTENT_LENGTH}")
logger.debug(f"[Config] SECRET_KEY {SECRET_KEY}")

# End of Do not modify
