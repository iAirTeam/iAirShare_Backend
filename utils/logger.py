import datetime

from quart import request
from loguru import logger
from logging import Logger

# Replace quart logger with loguru
Logger.manager.loggerDict['quart.app'] = logger


def request_log():
    logger.debug(f"{datetime.datetime.now()} [{request.method}] {request.url}")
