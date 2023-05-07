import unittest

from storage import AdminFileAPI
from config import ADMIN_CODE

access = AdminFileAPI(repo_id='tests', token=ADMIN_CODE, create_not_exist=True)
access.mapping.clear()
