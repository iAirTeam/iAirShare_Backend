import unittest

from app import app
from config import BACKEND_Name, SERVER_Version, SERVER_VersionCode


class RootTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    async def test_query_info(self):
        response = await self.app.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(await response.json, {
            "name": BACKEND_Name,
            "versionCode": SERVER_VersionCode,
            "version": SERVER_Version,
        })


if __name__ == '__main__':
    unittest.main()
