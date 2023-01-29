import datetime
from time import time as now

from roles import Role


class AsUser:
    def __init__(self, name: str,
                 initscore: int = 100,
                 nick: str = None
                 ):
        self.name = name
        self.nick = nick
        self.creation_date = datetime.date.fromtimestamp(now())
        self.score = initscore
        self.roles: Role[]
