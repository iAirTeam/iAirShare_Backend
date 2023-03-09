import unittest
import json

from app import app
from config import SERVER_NAME


class RootTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def test_query_info(self):
        response = self.app.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            "name": SERVER_NAME,
            "versionCode": 'alpha',
            "version": -3,
        })


if __name__ == '__main__':
    unittest.main()
