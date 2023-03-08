import unittest
from http import HTTPStatus
from io import BytesIO
from app import app
from copy import deepcopy
from random import randint
from os import path


class FileAPITest(unittest.TestCase):
    def setUp(self) -> None:  # Call when the test has created.
        self.app = app.test_client()
        self.test_data = {'file': (BytesIO(b'testMsg'), 'test file - space test')}

    def test_01_upload_public(self):
        """
        测试公共文件上传
        """

        response = self.app.put('/api/file/public/', data=deepcopy(self.test_data))  # upload file
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Upload failed")

    def test_02_upload_dir(self):
        """
        测试文件夹创建和上传在文件夹中
        """
        response_dir = self.app.put('/api/file/public/test dir/')  # create dir
        self.assertEqual(response_dir.status_code, HTTPStatus.CREATED, "Create dir failed")

        response = self.app.put('/api/file/public/test dir/', data=deepcopy(self.test_data))  # create file
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Upload failed")

        response_dir = self.app.put('/api/file/public/test dir/114514/')  # create dir
        self.assertEqual(response_dir.status_code, HTTPStatus.CREATED, "Create dir failed")

        response_dir = self.app.put('/api/file/public/test dir/114514/191810/')  # create dir
        self.assertEqual(response_dir.status_code, HTTPStatus.CREATED, "Create dir failed")

        string = ''.join([chr(randint(0, 0x10ffff)) for _ in range(0, 100)])
        test_data = deepcopy(self.test_data)

        test_data['file'] = (BytesIO(b'testMsg'), f'哼哼哼啊啊啊啊啊-{string}')
        
        response = self.app.put(f'/api/file/public/test dir/114514/191810/', data=test_data)  # create file
        self.assertEqual(response.status_code, HTTPStatus.CREATED, "Upload failed")

    # def test_get_file_public(self):
    #     response = self.app.get('/api/file/public/test_file')
    #
    #     self.assertEqual(response.status_code, 200, "Bad Status Code")
    #     self.assertEqual(response.data.decode('UTF-8'), 'Hello world')
    #
    # def test_02_upload2_public(self):
    #     data = {'file': (BytesIO(b'Hello world'), 'test_file_in_dir')}
    #
    #     self.app.put('/api/file/public/dir1/')  # create file dir: dir1
    #
    #     response = self.app.put('/api/file/public/dir1/', data=data)
    #
    #     self.assertEqual(response.status_code, 201, "Bad Status Code")
    #
    # def test_03_get_file2_public(self):
    #     response = self.app.get('/api/file/public/dir1/test_file_in_dir')
    #
    #     self.assertEqual(response.status_code, 200, "Bad Status Code")
    #     self.assertEqual(response.data.decode('UTF-8'), 'Hello world')
    #
    # def test_list_dir_public(self):
    #     response = self.app.get('/api/file/public/')
    #
    #     d_next = response.json['data']['next']
    #
    #     if d_next <= 0:
    #         self.assertNotEqual(d_next, -114514, 'Something went wrong!')
    #
    #     while d_next > 0:
    #         response = self.app.get(f'/api/file/public/?next={d_next}')
    #
    #         d_next = response.json['data']['next']
    #
    #     self.assertNotEqual(response.json['data']['next'], -114514, 'Something went wrong!')
    #     self.assertEqual(response.json['data']['next'], 0, "Invalid next value")


if __name__ == '__main__':
    unittest.main()
