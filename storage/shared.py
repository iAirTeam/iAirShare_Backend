from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

SECRET_KEY: str = 'AirShare'

sqlalchemy: Optional[SQLAlchemy] = None

app: Flask
