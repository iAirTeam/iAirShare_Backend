import datetime

from quart import request
from loguru import logger


def request_log():
    logger.debug(f"{datetime.datetime.now()} [{request.method}] {request.url}")
