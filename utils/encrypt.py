import hashlib
from array import array
from mmap import mmap
from config import SECRET_KEY


def custom_hash(data: bytes | bytearray | memoryview | array | mmap) -> bytes:
    return hashlib.sha384(data).digest() + hashlib.sha256(data).digest()


def hash_file(data: bytes | bytearray | memoryview | array | mmap) -> str:
    return hashlib.sha3_512(custom_hash(data + SECRET_KEY.encode('UTF-8'))).hexdigest()
