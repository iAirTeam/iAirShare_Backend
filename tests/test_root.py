import unittest

from app import app
from config import AIRSHARE_BACKEND_NAME


class RootTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    async def test_query_info(self):
        response = await self.app.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(await response.json, {
            "name": AIRSHARE_BACKEND_NAME,
            "versionCode": 'alpha',
            "version": -3,
        })


if __name__ == '__main__':
    unittest.main()
