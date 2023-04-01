import asyncio
import signal
from typing import Any

from hypercorn.asyncio import serve
from hypercorn.config import Config

from utils.create_app import create_app
import config as config

config = Config().from_object(config)

shutdown_event = asyncio.Event()


def _signal_handler(*_: Any) -> None:
    shutdown_event.set()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.add_signal_handler(signal.SIGTERM, _signal_handler)
loop.run_until_complete(
    serve(create_app(), config, shutdown_trigger=shutdown_event.wait)
)
