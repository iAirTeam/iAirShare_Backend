from config import ADMIN_CODE
from storage import AdminFileAPI

access = AdminFileAPI(repo_id='tests', token=ADMIN_CODE, create_not_exist=True)
access.mapping.clear()
