import unittest
from http import HTTPStatus
from io import BytesIO

from app import app
from storage import AdminFileAPI
from config import ADMIN_CODE


class FileAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()
        resp = self.app.get('/')
        self.failUnlessEqual(resp.content_type, 'application/json')
        self.failUnlessEqual(('name', 'versionCode', 'version'), tuple(resp.json.keys()))

    def test_01_1_upload(self):
        data = {'file': (BytesIO(f"test_01".encode('UTF-8')), 'test_01')}

        resp = self.app.put('/api/file/tests/', data=data)

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual(resp.json['status'], 200, resp.json['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    def test_01_2_get(self):
        resp = self.app.get('/api/file/tests/test_01')

        if resp.content_type == 'application/json':
            self.assertTrue(False, resp.json)
            return None

        self.assertEqual(resp.data, b'test_01')

    def test_02_dir1(self):
        response = self.app.get('/api/file/tests/')

        d_next = response.json['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            response = self.app.get(f'/api/file/tests/?next={d_next}')

            d_next = response.json['data']['next']

        self.assertNotEqual(response.json['data']['next'], -114514, 'Something went wrong!')
        self.assertEqual(response.json['data']['next'], 0, "Invalid next value")

    def test_02_dir2(self):
        response = self.app.get('/api/file/tests/')

        d_next = response.json['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            response = self.app.get(f'/api/file/public/?next={d_next}')

            d_next = response.json['data']['next']

        self.assertNotEqual(response.json['data']['next'], -114514, 'Something went wrong!')
        self.assertEqual(response.json['data']['next'], 0, "Invalid next value")


if __name__ == '__main__':
    unittest.main()
