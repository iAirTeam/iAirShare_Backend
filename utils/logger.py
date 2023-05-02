import ever_loguru
from loguru import logger
from quart import request

ever_loguru.install_class()

logger.patch(lambda record: record['extra'].update(req=request))

ever_loguru.install()


def request_log():
    with logger.contextualize(extra={**request}):
        logger.debug("[{datetime.datetime.now()}] ({extra[remote_addr]})[{extra[method]}] {extra[url]}")
