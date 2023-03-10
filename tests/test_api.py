import unittest
from http import HTTPStatus
from io import BytesIO

from app import app
from storage import AdminFileAPI, FileMapping
from config import ADMIN_CODE


class FileAPITest(unittest.TestCase):
    async def setUp(self) -> None:
        self.app = app.test_client()
        resp = await self.app.get('/')
        self.failUnlessEqual(resp.content_type, 'application/json')
        self.failUnlessEqual(('name', 'versionCode', 'version'), tuple(resp.json.keys()))

    async def test_01_1_upload(self):
        """
        根目录上传
        """

        data = {'file': (BytesIO(f"test_01".encode('UTF-8')), 'test_01')}

        resp = await self.app.put('/api/file/tests/', data=data)

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual(resp.json['status'], 200, resp.json['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_01_2_get(self):
        """
        根目录获取(单个文件)
        """

        resp = await self.app.get('/api/file/tests/test_01')

        if resp.content_type == 'application/json':
            self.assertTrue(False, resp.json)
            return None

        self.assertEqual(resp.data, b'test_01')

    async def test_01_3_dir1(self):
        """
        列出根目录(tests/)
        """
        response = await self.app.get('/api/file/tests/')

        d_next = response.json['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            response = await self.app.get(f'/api/file/tests/?next={d_next}')

            d_next = response.json['data']['next']

        self.assertNotEqual(response.json['data']['next'], -114514, 'Something went wrong!')
        self.assertEqual(response.json['data']['next'], 0, "Invalid next value")

    async def test_02_01_create_dir(self):
        """
        创建文件夹
        """

        resp = await self.app.put('/api/file/tests/test_02/')

        # resp.json 即将返回数据转换为 json
        # resp.data 即返回数据
        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual(resp.json['status'], 200, resp.json['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_02_02_upload_to_dir(self):
        """
        向文件夹内上传文件
        """
        data = {'file': (BytesIO(b"test_02_2"), 'test_02_2')}

        resp = await self.app.put('/api/file/tests/test_02/', data=data)

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual(resp.json['status'], 200, resp.json['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_02_03_dir(self):
        """
        列出文件夹(tests/test_02/)内容
        """

        response = await self.app.get('/api/file/tests/test_02/')

        lst: FileMapping = [*response.json['data']['files']]

        d_next = response.json['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            lst.append(*response.json['data']['files'])

            response = await self.app.get(f'/api/file/tests/test_02/?next={d_next}')

            d_next = response.json['data']['next']

        self.assertNotEqual(response.json['data']['next'], -114514, 'Something went wrong with next!')
        self.assertEqual(response.json['data']['next'], 0, "Invalid next value")
        self.assertIn('test_02_2', tuple(map(lambda x: x['file_name'], lst)))


if __name__ == '__main__':
    unittest.main()
