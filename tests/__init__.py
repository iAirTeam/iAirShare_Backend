import unittest

from storage import AdminFileAPI
from config import ADMIN_CODE

if __name__ == '__main__':
    from tests.test_api import FileAPITest
    from tests.test_root import RootTest
    from tests.test_fileapi import FileAPITestCase

    unittest.main()

access = AdminFileAPI(repo_id='tests', token=ADMIN_CODE)
access.config['mapping'].clear()
