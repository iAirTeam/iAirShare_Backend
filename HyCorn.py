import asyncio
import signal
from typing import Any

from hypercorn.asyncio import serve
from hypercorn.config import Config

from helpers.create_app import create_app
import config as config
from utils.logger import logger, LoggingLoguruWrapper

config = Config().from_object(config)
config.logger_class = LoggingLoguruWrapper

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

shutdown_event = asyncio.Event()


def _signal_handler(*_: Any) -> None:
    logger.debug("Shutdown event triggered.")
    shutdown_event.set()


app = create_app()


@app.after_serving
def end_serving():
    logger.info("Server is shutting down...")


loop.add_signal_handler(signal.SIGTERM, _signal_handler)
loop.add_signal_handler(signal.SIGINT, _signal_handler)
loop.add_signal_handler(signal.SIGQUIT, _signal_handler)
# noinspection PyTypeChecker
loop.run_until_complete(
    serve(app, config, shutdown_trigger=shutdown_event.wait)
)
