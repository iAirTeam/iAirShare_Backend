from typing import Optional

from quart_sqlalchemy import SQLAlchemy
from quart import Quart

SECRET_KEY: str = 'AirShare'

sqlalchemy: Optional[SQLAlchemy] = None

app: Quart
