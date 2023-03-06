import unittest
from io import BytesIO
from app import app


class FileAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()

    def test_a_upload_public(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file')}

        response = self.app.put('/api/file/public/', data=data)

        self.assertEqual(response.status_code, 201, "Bad Status Code")

    def test_get_file_public(self):
        response = self.app.get('/api/file/public/test_file')

        self.assertEqual(response.status_code, 200, "Bad Status Code")
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')

    def test_aa_upload2_public(self):
        data = {'file': (BytesIO(b'Hello world'), 'test_file_in_dir')}

        response = self.app.put('/api/file/public/dir1/')

        response = self.app.put('/api/file/public/dir1/', data=data)

        self.assertEqual(response.status_code, 201, "Bad Status Code")

    def test_b_get_file2_public(self):
        response = self.app.get('/api/file/public/dir1/test_file_in_dir')

        self.assertEqual(response.status_code, 200, "Bad Status Code")
        self.assertEqual(response.data.decode('UTF-8'), 'Hello world')

    def test_list_dir_public(self):
        response = self.app.get('/api/file/public/')

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
