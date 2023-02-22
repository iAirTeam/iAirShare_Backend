from __future__ import annotations

from logging import getLogger as _getLogger
from flask_sqlalchemy import SQLAlchemy

logger = _getLogger("iAirShare")

image_ext = [
    '.png', '.jpg', '.jpeg', '.apng', '.avif', '.bmp', '.gif', '.ico', '.cur', '.jfif',
    '.pjpeg', '.pjp', '.svg', '.tif', '.tiff', '.webp'
]

video_ext = [
    '.mp4', '.webm', '.avi', '.mpeg', '.mkv', '.mov'
]

audio_ext = [
    '.mp3', '.wma', '.rm', '.wav', '.flac', '.ogg'
]

database: SQLAlchemy | None = None
