import unittest
from storage import *


class FileAPITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FileAPIPrivate('tests', create_not_exist=True)
        self.file = File(file_name='foo', pointer='2333')

    def test_aa_init_repo(self):
        self.assertTrue(self.repo.repo_exist)
        self.assertEqual(self.repo.repo_name, 'tests')

    def test_bb_init_file(self):
        self.assertEqual(self.file.file_name, 'foo')
        self.assertEqual(self.file.pointer, '2333')
        self.assertIsNotNone(self.file.file_property)

    def test_set_file(self):
        result = self.repo.set_file('/test', self.file)
        self.assertEqual(result, ['test'])

    def test_set_file_not_exist(self):
        result = self.repo.set_file('/bad_dir/bad_f', self.file)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
