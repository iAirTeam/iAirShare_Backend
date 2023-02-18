import json
import pathlib
import random
from typing import Optional, TypedDict, Self, Type, Literal, Union, Tuple, List, Dict
from abc import abstractmethod, ABC
from io import BytesIO
import atexit

from werkzeug.datastructures import FileStorage

from .vars import *
from .exceptions import *
from .encrypt import custom_hash, hash_file

RepoId = str
FileId = str
FileName = str

iter_storage = {}

File = FileId | Type["FileMapping"]
FileMapping = Dict[FileName, File]


class RepoConfigStructure(TypedDict):
    repo_name: str
    permission_nodes: dict[str, bool | Type["permission_nodes"]]
    access_token: str
    mapping: FileMapping


class FileAPIBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def _queries(self, file_id) -> BytesIO | None:
        """
        通过 文件ID 获取文件数据
        :param file_id: 文件ID
        :return: 文件数据(BytesIO) 不存在时为 None
        """
        pass

    @abstractmethod
    def upload_repo_file(self, path: Optional[str], file: FileStorage) -> tuple[str, tuple]:
        """
        向 Repo 上传文件
        :param path: 目录位置
        :param file: 文件(Flask Werkzeug的FileStorage)
        :return: file_hash 和 path 分割结果
        """
        pass

    @abstractmethod
    def list_repo_dir(self, path: Optional[str]) -> list[str] | None:
        """
        获取 Repo 中 path 目录下的文件(夹) 的列表
        :param path: 目录位置
        :return: 文件列表 否则为 None
        """
        pass

    def next_repo_dir(self, path: Optional[str], d_next: int = None):
        """
        获取 Repo 中 path 目录下 的 一个文件(夹)
        :param path: 目录位置
        :param d_next: 获取下一个文件(夹)用的标识
        :return: 文件, 总数, 获取下一个的标识
        """
        pass

    @abstractmethod
    def quires_repo_file(self, path: str) -> FileId:
        """
        通过 path 获取 文件ID
        :param path: 文件路径
        :return: 文件ID
        """
        pass

    @abstractmethod
    def unlink_repo_file(self, path: str) -> FileId:
        """
        移除目标 path 指向的内容 (≈可以理解为删除文件)
        :param path: 文件路劲
        :return:
        """
        pass

    @abstractmethod
    def move_repo_file(self, old_path: str, new_path: str) -> bool:
        """
        移动目标 old_path 指向的内容到 new_path (≈可以理解为移动文件(夹))
        :param old_path: 欲移动文件(夹)位置
        :param new_path: 目标位置
        :return: 是否成功
        """
        pass

    @abstractmethod
    def can_access_repo(self, access_token) -> bool:
        pass

    @property
    @abstractmethod
    def repo_exist(self) -> bool:
        pass


class FileAPIDrive(FileAPIBase, ABC):

    def __init__(self, create_not_exist=True, repo_name=None):
        super().__init__()

        base_dir = pathlib.Path('instance')
        file_dir = base_dir / 'files'
        config_dir = base_dir / ('config' if not repo_name else repo_name.lower() + "_config.json")

        self.base_dir: pathlib.Path = pathlib.Path(base_dir)
        self.file_dir: pathlib.Path = pathlib.Path(file_dir)

        self.config: RepoConfigStructure = {
            "repo_name": repo_name,
            "mapping": {},
            "permission_nodes": {},
            "access_token": ""
        }

        self.config_dir: pathlib.Path = pathlib.Path(config_dir)

        self.access_token: str = None

        if config_dir.exists():
            atexit.register(self._save_storage)

        if not file_dir.exists() and create_not_exist:
            file_dir.mkdir(parents=True)
        if not base_dir.is_dir() and create_not_exist:
            base_dir.unlink()
            file_dir.mkdir(parents=True, exist_ok=True)

        if not config_dir.exists() and create_not_exist:
            with config_dir.open('w') as file:
                json.dump(self.config, file)
        elif not config_dir.is_file() and create_not_exist:
            config_dir.unlink(missing_ok=True)
            with config_dir.open('w') as file:
                json.dump(self.config, file)
        else:
            try:
                with config_dir.open('r+', encoding='UTF-8') as file:
                    try:
                        self.config: RepoConfigStructure = json.load(file)
                    except ValueError:
                        json.dump(self.config, file)
            except FileNotFoundError:
                pass

        self.mapping = self.config['mapping']

    def _save_storage(self):
        with open(self.config_dir, 'w', encoding='UTF-8') as file:
            json.dump(self.config, file, ensure_ascii=False)

    @classmethod
    def _set_by_path(cls, d, path, val):
        if len(path) == 1:
            old_val = None
            if path[0] in d:
                old_val = d[path[0]]
            d[path[0]] = val
            return old_val
        else:
            key = path.pop(0)
            if key not in d:
                d[key] = {}
            return cls._set_by_path(d[key], path, val)

    @classmethod
    def _get_by_path(cls, d, path):
        if len(path) == 1:
            if path[0] == '':
                return d
            return d[path[0]]
        else:
            key = path.pop(0)
            return cls._get_by_path(d[key], path)

    def _queries(self, file_id) -> BytesIO | None:
        file_path = pathlib.Path(self.file_dir) / file_id
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as file:
            return BytesIO(file.read())

    def upload_repo_file(self, path: str, file: FileStorage) -> tuple[str, list[str]]:
        io = BytesIO()
        file.save(io)
        byte_file = io.getvalue()

        file_hash = hash_file(byte_file)

        if not (self.file_dir / file_hash).exists():
            with open(self.file_dir / file_hash, 'wb') as file:
                file.write(byte_file)

        keys = path.lstrip('/').split('/')

        if keys[0]:
            self._set_by_path(self.mapping, keys + [file.filename], file_hash)
        else:
            self.mapping.update({file.filename: file_hash})

        return file_hash, keys

    def list_repo_dir(self, path: str) -> list[str] | None:
        keys = path.lstrip('/').split('/')

        directory_data = self.mapping

        if keys:
            directory_data = self._get_by_path(self.mapping, keys)

        if not isinstance(directory_data, dict):
            return None

        result = []
        for key in directory_data:
            data = directory_data[key]
            if isinstance(data, str):
                result.append(key)
            elif isinstance(data, dict):
                result.append('[directory]')
            else:
                result.append('[undefined]')

        return result

    def next_repo_dir(self, path: Optional[str], d_next: int = None):
        if not d_next:
            dir_iter = self.list_repo_dir(path)
            iter_id = int(str(abs(hash(str(dir_iter)) + hash(path)))[:6])
            iter_id += random.randint(-2000, 1000)
            if len(iter_storage) > 300:
                for _ in range(200):
                    iter_storage.popitem()
            iter_storage.update({iter_id: (iter(dir_iter), len(dir_iter))})
            try:
                return next(iter_storage[iter_id][0]), len(dir_iter), iter_id
            except StopIteration:
                return None, 0, 0
        else:
            dir_iter = None
            try:
                dir_iter = iter_storage.pop(d_next)
            except KeyError:
                pass

            if not dir_iter:
                return None, 0, -114514

            try:
                value = next(dir_iter[0])
                iter_id = int(str(abs(hash(str(dir_iter) + str(value)) + hash(path)))[:8])
                iter_id += random.randint(-2000, 1000)
                iter_storage.update({iter_id: (dir_iter[0], dir_iter[1])})
                return value, dir_iter[1], iter_id
            except StopIteration:
                return None, 0, 0

    def quires_repo_file(self, path) -> FileId | None:
        keys = path.split('/')
        try:
            file_id = self._get_by_path(self.mapping, keys)
            if not isinstance(file_id, str):
                if isinstance(file_id, dict):
                    return '[Directory]'
                return None
            return file_id
        except KeyError:
            return None

    def unlink_repo_file(self, path) -> FileId:
        return self._set_by_path(self.mapping, path, None)

    def move_repo_file(self, old_path: str, new_path: str) -> bool:
        try:
            self._get_by_path(self.mapping, old_path)
        except KeyError:
            return Faose
        try:
            self._get_by_path(self.mapping, new_path)
        except KeyError:
            self._set_by_path(self.mapping, new_path, self._set_by_path(self.mapping, old_path, None))
            return True
        else:
            return False

    def __getattribute__(self, item: str):
        import inspect
        ret_item = super().__getattribute__(item)
        if item in (
                'can_access_repo',
                '_save_storage'
        ):
            return ret_item

        import inspect
        frame = inspect.currentframe()

        if frame.f_back.f_code.co_filename == frame.f_code.co_filename or callable(ret_item) and \
                not (item.endswith('_dir') and item in (
                        'config',
                        'mapping'
                )):
            return ret_item

        return ret_item if self.can_access_repo(self.access_token) \
            else None


class FileAPIPublic(FileAPIDrive):
    public_instance: "FileAPIPublic" = None

    def __new__(cls, *args, **kwargs):
        if cls.public_instance:
            return cls.public_instance

        cls.public_instance = super().__new__(cls, *args, **kwargs)
        return cls.public_instance

    def __init__(self):
        super().__init__(repo_name='Public')

    def can_access_repo(self, access_token) -> bool:
        return True

    def repo_exist(self) -> bool:
        return True


class FileAPIPrivate(FileAPIDrive):
    @property
    def repo_exist(self) -> bool:
        return self.config_dir.exists() and self.file_dir.exists()

    def __init__(self, repo_id: str, access_token: str = '', create_not_exist=False):
        super().__init__(create_not_exist=create_not_exist, repo_name=repo_id)
        if self.can_access_repo(access_token):
            self.access_token = access_token

    def can_access_repo(self, access_token) -> bool:
        return access_token == self.config['access_token']
