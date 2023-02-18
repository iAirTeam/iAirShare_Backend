import unittest
from app import app
import json


class RootTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def test_query_info(self):
        response = self.app.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {
            "name": "AirShare",
            "versionCode": 'alpha',
            "version": -3,
        })


if __name__ == '__main__':
    unittest.main()
