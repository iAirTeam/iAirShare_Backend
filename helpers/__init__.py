from utils.response import *


def serialize(obj):
    if isinstance(obj, set):
        return frozenset(obj)
    elif isinstance(obj, frozenset):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.timestamp()
    else:
        return obj.__dict__
