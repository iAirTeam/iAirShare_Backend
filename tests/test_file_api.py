import unittest
from io import BytesIO
from app import app
import json


class FileAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def test_query_info(self):
        response = self.app.put('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data),
                         {
                             "name": "AirShare",
                             "versionCode": 'alpha',
                             "version": -3,
                         }
                         )

    def test_a_upload(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file')}

        response = self.app.put('/file/public', data=data)

        self.assertEqual(response.status_code, 201, "Bad Status Code")

    def test_get_file(self):
        response = self.app.get('/file/public/test_file')

        self.assertEqual(response.status_code, 200, "Bad Status Code")
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')

    def test_a_upload2(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file_in_dir')}

        response = self.app.put('/file/public/dir1', data=data)

        self.assertEqual(response.status_code, 201, "Bad Status Code")

    def test_get_file2(self):
        response = self.app.get('/file/public/dir1/test_file_in_dir')

        self.assertEqual(response.status_code, 200, "Bad Status Code")
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')

    def test_list_dir(self):
        response = self.app.get('/file/public')

        data = json.loads(response.data)['data']

        d_next = data['next']

        if d_next <= 0:
            self.assertNotEqual(data['next'], -114514, 'Something went wrong!')

        while d_next > 0:
            response = self.app.get(f'/file/public?next={d_next}')

            data = json.loads(response.data)['data']

            d_next = data['next']

        self.assertNotEqual(data['next'], -114514, 'Something went wrong!')
        self.assertEqual(data['next'], 0, "Invalid next value")
