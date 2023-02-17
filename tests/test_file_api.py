import unittest
from io import BytesIO
from app import app


class FileAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def test_a_upload(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file')}

        response = self.app.put('/file/public', data=data)

        self.assertEqual(response.status_code, 201)

    def test_get_file(self):
        response = self.app.get('/file/public/test_file')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')

    def test_a_upload2(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file_in_dir')}

        response = self.app.put('/file/public/dir1', data=data)

        self.assertEqual(response.status_code, 201)

    def test_get_file2(self):
        response = self.app.get('/file/public/dir1/test_file_in_dir')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')
