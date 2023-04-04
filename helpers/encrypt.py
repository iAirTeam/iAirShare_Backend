from __future__ import annotations

import hashlib
from array import array
from mmap import mmap
from storage.shared import SECRET_KEY


def custom_hash(data: bytes | bytearray | memoryview | array | mmap) -> bytes:
    return hashlib.sha384(data).digest() + hashlib.sha256(bytes(len(data))).digest() + hashlib.sha256(
        SECRET_KEY.encode('UTF-8')).digest()


def hash_file(data: bytes | bytearray | memoryview | array | mmap) -> str:
    return hashlib.sha3_512(custom_hash(data)).hexdigest()
