import unittest
from http import HTTPStatus
from io import BytesIO

from quart.datastructures import FileStorage

from app import app
from storage import FileMapping


class FileAPITest(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.app = app
        self.client = self.app.test_client()

    async def test_01_1_upload(self):
        """
        根目录上传
        """

        file = {"file": FileStorage(
            stream=BytesIO(f"test_01".encode('UTF-8')),
            filename="test_01",
            content_type="text/plain"
        )}

        resp = await self.client.put('/api/file/tests/', files=file, headers={
            "Content-Type": "multipart/form-data"
        })

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual((await resp.json)['status'], 200, (await resp.json)['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_01_2_get(self):
        """
        根目录获取(单个文件)
        """

        resp = await self.client.get('/api/file/tests/test_01')

        if resp.content_type == 'application/json':
            self.assertTrue(False, await resp.json)
            return None

        self.assertEqual(await resp.data, b'test_01')

    async def test_01_3_dir1(self):
        """
        列出根目录(tests/)
        """

        response = await self.client.get('/api/file/tests/')

        d_next = (await response.json)['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            response = await self.client.get(f'/api/file/tests/?next={d_next}')

            d_next = (await response.json)['data']['next']

        self.assertNotEqual((await response.json)['data']['next'], -114514, 'Something went wrong!')
        self.assertEqual((await response.json)['data']['next'], 0, "Invalid next value")

    async def test_02_01_create_dir(self):
        """
        创建文件夹
        """

        resp = await self.client.put('/api/file/tests/test_02/')

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual((await resp.json)['status'], 200, (await resp.json)['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_02_02_upload_to_dir(self):
        """
        向文件夹内上传文件
        """

        file = {'file': FileStorage(
            stream=BytesIO(b"test_02_2"),
            filename='test_02_2',
            content_type='text/plain'
        )}

        resp = await self.client.put('/api/file/tests/test_02/', files=file, headers={
            "Content-Type": "multipart/form-data"
        })

        self.assertEqual(resp.content_type, 'application/json', 'Bad Content-Type')
        self.assertEqual((await resp.json)['status'], 200, (await resp.json)['msg'])
        self.assertEqual(resp.status_code, HTTPStatus.CREATED)

    async def test_02_03_dir(self):
        """
        列出文件夹(tests/test_02/)内容
        """

        response = await self.client.get('/api/file/tests/test_02/')

        lst: FileMapping = [*(await response.json)['data']['files']]

        d_next = (await response.json)['data']['next']

        if d_next <= 0:
            self.assertNotEqual(d_next, -114514, 'Something went wrong!')

        while d_next > 0:
            lst.append(*(await response.json)['data']['files'])

            response = await self.client.get(f'/api/file/tests/test_02/?next={d_next}')

            d_next = (await response.json)['data']['next']

        self.assertNotEqual((await response.json)['data']['next'], -114514, 'Something went wrong with next!')
        self.assertEqual((await response.json)['data']['next'], 0, "Invalid next value")
        self.assertIn('test_02_2', tuple(map(lambda x: x['file_name'], lst)))


if __name__ == '__main__':
    unittest.main()
