import unittest
from storage import *


# Copyright iAirTeam (c) 2023
# All Rights Released. 保留所有权力.
# 测试内容不代表最终品质.


class FileAPITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FileAPIPrivate('tests', create_not_exist=True)
        self.failUnless(self.repo.repo_exist)
        self.assertEqual(self.repo.repo_name, 'tests')

        self.file = File(file_name='foo', pointer='2333')
        self.failUnlessEqual(self.file.file_name, 'foo')
        self.failUnlessEqual(self.file.pointer, '2333')
        self.assertIsNotNone(self.file.file_property)

        self.dir = Directory(file_name='bar')

        self.failUnlessEqual(self.dir.file_name, 'bar')
        self.failUnlessEqual(self.dir.pointer, {})
        self.assertIsNone(self.dir.file_property)

    def test_02_2_set_file(self):
        result = self.repo.set_file('/', self.file)
        self.assertEqual(result, [''])

    def test_02_2_set_file_udf(self):
        result = self.repo.set_file('/bad_dir/bad_f', self.file)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
