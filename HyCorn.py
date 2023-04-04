import asyncio
import signal
import time
from typing import Any

from hypercorn.asyncio import serve
from hypercorn.config import Config

from helpers.create_app import create_app
import config as config
from utils.logger import logger


class LoguruWrapper:
    def __init__(self, another):
        self.another = another

    def _attrAsyncWrapper(self, func):
        async def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return _wrapper

    def __getattr__(self, item):
        return self._attrAsyncWrapper(logger.__getattribute__(item))


config = Config().from_object(config)
config.logger_class = LoguruWrapper

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

shutdown_event = asyncio.Event()


def _signal_handler(*_: Any) -> None:
    logger.debug("Shutdown event triggered.")
    logger.info("Wait for the server to shutdown...")
    shutdown_event.set()
    logger.success("Server has been closed.")


loop.add_signal_handler(signal.SIGTERM, _signal_handler)
loop.add_signal_handler(signal.SIGINT, _signal_handler)
loop.add_signal_handler(signal.SIGQUIT, _signal_handler)
loop.run_until_complete(
    serve(create_app(), config, shutdown_trigger=shutdown_event.wait)
)
