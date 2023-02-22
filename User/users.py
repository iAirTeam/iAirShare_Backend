# import datetime
# import os.path
# from time import time as now
# from json i
#
# from .roles import Role
#
# users: set["AsUser"] = set()
#
#
# class AsUser:
#     def __init__(self, name: str,
#                  score: int = 100,
#                  nick: str = None
#                  ):
#         self.id = len(users) + 3001
#         self.name = name
#         self.nick = nick
#         self.creation_date = datetime.datetime.now()
#         self.score = score
#         self.roles: list[Role] = []
#
#     def __hash__(self):
#         return f"{self.name}__{self.creation_date}#{self.id}"
#
#     def __repr__(self):
#         return f"{self.name}#{self.id}"
#
#
# if os.path.exists("user_data.dat") and os.path.isfile("user_data.dat"):
#     try:
#         with open('user_data') as f:
#             users = load(f)
#     finally:
#         if users is None:
#             users = set()
