import logging
import sys

from loguru import logger
from quart import request


class LoggingLoguruWrapper:
    def __init__(self, __placeholder: str):
        pass

    @staticmethod
    def _async_wrapper(func):
        async def __logger_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return __logger_wrapper

    def __getattr__(self, item):
        return self._async_wrapper(getattr(logger.opt(depth=2), item))


class LoguruLoggingHandler(logging.Handler):
    """
    Add logging handler to augment python stdlib logging.

    Logs which would otherwise go to stdlib logging are redirected through
    loguru.
    """

    @logger.catch(default=True, onerror=lambda _: sys.exit(1))
    def emit(self, record):
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = (lambda: sys._getframe(6) if hasattr(sys, "_getframe") else None)(), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logger.patch(lambda record: record['extra'].update(req=request))

callHandlers_func = sys.modules['logging'].Logger.callHandlers


def _callHandlers_wrapper(original, record):
    if hasattr(original, "handlers"):
        if getattr(original, "handlers"):
            setattr(original, "handlers", [LoguruLoggingHandler()])

    if callable(callHandlers_func):
        callHandlers_func(original, record)


sys.modules['logging'].Logger.callHandlers = _callHandlers_wrapper


def request_log():
    with logger.contextualize(extra={**request}):
        logger.debug("[{datetime.datetime.now()}] ({extra[remote_addr]})[{extra[method]}] {extra[url]}")
