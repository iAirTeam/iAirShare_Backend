from enum import Enum


class Role(Enum):
    Admin = 0x010
    User = 0x200
    Guest = 0x500
