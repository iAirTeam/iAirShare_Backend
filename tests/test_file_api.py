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

    def test_get(self):
        response = self.app.get('/file/public/test_file')
        self.assertEqual(response.status_code, 200)
