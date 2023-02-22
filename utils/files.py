from __future__ import annotations

import json
import pathlib
import random
import time
import sys
from typing import Optional, TypedDict, Self, Type, Literal, Union, Tuple, List, Dict

if sys.version_info < (3, 11):  # Support for lower version
    from typing_extensions import NotRequired, TypedDict

from typing_extensions import Required, NotRequired
from abc import abstractmethod, ABC
from io import BytesIO
import atexit

from werkzeug.datastructures import FileStorage
from strongtyping.strong_typing import TypeMisMatch, match_typing, match_class_typing
import sqlalchemy as sa

from .var import database
from .exceptions import *
from .encrypt import custom_hash, hash_file

RepoId = str
FileId = Optional[str]
FileName = str

iter_storage = {}


@match_class_typing
class FileStaticInfo(TypedDict):
    file_id: FileId
    file_size: int
    property: "FileStaticProperty"


@match_class_typing
class FileSpecialInfo(TypedDict):
    file_id: FileId
    mimetype: str
    file_size: int
    last_update: int


@match_class_typing
class FileStaticProperty(TypedDict, total=False):
    detected_file_type: Optional[str]
    i_width: int
    i_height: int
    v_fps_avg: int
    v_bitrate: int
    v_a_bitrate: int
    av_length_sec: float
    prop_ver: int


File = Union[FileSpecialInfo, "FileMapping"]
FileMapping = Dict[FileName, File]


@match_class_typing
class RepoConfigAccessStructure(TypedDict):
    repo_name: str
    permission_nodes: dict[str, bool | Type["permission_nodes"]]
    access_token: str
    mapping: FileMapping


class FileAPIImpl(ABC):

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
    def list_repo_dir(self, path: Optional[str]) -> Optional[list[str]]:
        """
        获取 Repo 中 path 目录下的文件(夹) 的列表
        :param path: 目录位置
        :return: 文件列表 否则为 None
        """
        pass

    def next_repo_dir(self, path: Optional[str], d_next: int = None):
        """
        获取 Repo 中 path 目录下 的 一个文件(夹)
        不强制要求实现
        :param path: 目录位置
        :param d_next: 获取下一个文件(夹)用的标识
        :return: 文件, 总数, 获取下一个的标识
        """
        pass

    @abstractmethod
    def quires_repo_file(self, path: str) -> Optional[FileStaticInfo] | str:
        """
        根据 路径 获取文件信息
        :param path: 文件路径
        :return: FileID(文件ID) (不存在时为空)
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
        """是否可以访问存储库"""
        pass

    @property
    @abstractmethod
    def repo_exist(self) -> bool:
        """存储库是否存在"""
        pass


# noinspection PyUnusedLocal
class FileAPIStorage(ABC):
    @abstractmethod
    def __init__(self, create_not_exist: bool):
        """
        :param create_not_exist: 当不存在时创建
        """
        pass

    @abstractmethod
    def _upload(self, file: FileStorage) -> FileStaticInfo:
        """
        通过 file 上传文件
        :param file: Flask Werkzeug FileStorage 实例
        :return: FileStaticInfo
        """
        pass

    @abstractmethod
    @match_class_typing
    def _queries(self, file_id: FileId) -> Optional[BytesIO]:
        """
        通过 文件ID 获取文件数据
        :param file_id: 文件ID
        :return: 文件数据(BytesIO) 不存在时为 None
        """
        pass

    def get_file(self, file_info: FileSpecialInfo | FileStaticInfo) -> Optional[BytesIO]:
        """
        通过文件信息获取文件数据
        :param file_info: 文件信息(如FileInfo)
        :return: 文件数据(BytesIO) 不存在时为 None
        """
        return self._queries(file_info['file_id'])


# noinspection PyUnusedLocal
@match_class_typing
class FileAPIConfig(ABC):
    def __init__(self, repo_name: str, create_not_exist: bool):
        """
        :param create_not_exist: 当不存在时创建
        :param repo_name: 存储库名称
        """
        pass

    @property
    @abstractmethod
    def repo_name(self) -> str:
        pass

    @property
    @abstractmethod
    def config(self) -> RepoConfigAccessStructure:
        pass

    @property
    def mapping(self) -> FileMapping:
        return self.config['mapping']


class FileAPIDriveBase:
    def __init__(self):
        base_dir = pathlib.Path('instance')
        file_dir = base_dir / 'files'

        self.base_dir: pathlib.Path = pathlib.Path(base_dir)
        self.file_dir: pathlib.Path = pathlib.Path(file_dir)


class FileAPIConfigDrive(FileAPIDriveBase, FileAPIConfig, ABC):
    def __init__(self, repo_name: str, create_not_exist=True):
        super().__init__()

        self._config: RepoConfigAccessStructure = {
            "repo_name": repo_name,
            "mapping": {},
            "permission_nodes": {},
            "access_token": ""
        }

        config_dir = self.base_dir / f"{repo_name.lower() + '_' if repo_name else ''}config.json"


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
                        self._config: RepoConfigAccessStructure = json.load(file)
                    except ValueError:
                        json.dump(self.config, file)
            except FileNotFoundError:
                pass

        if config_dir.exists():
            atexit.register(self._save_storage)

        self.config_dir = config_dir

        self._mapping = self.config['mapping']

    def _save_storage(self):
        with open(self.config_dir, 'w', encoding='UTF-8') as file:
            json.dump(self.config, file, ensure_ascii=False)

    def repo_name(self) -> str:
        return self._config['repo_name']

    @property
    def config(self) -> RepoConfigAccessStructure:
        return self._config

    @property
    def mapping(self):
        return self._mapping


class FileAPIStorageDrive(FileAPIDriveBase, FileAPIStorage, ABC):
    def __init__(self, repo_name: str, create_not_exist=True):
        super().__init__(repo_name=repo_name, create_not_exist=create_not_exist)

        self.access_token: Optional[str] = None

        if not self.file_dir.exists() and create_not_exist:
            self.file_dir.mkdir(parents=True)
        if not self.base_dir.is_dir() and create_not_exist:
            self.base_dir.unlink()
            self.file_dir.mkdir(parents=True, exist_ok=True)

    def _queries(self, file_id) -> Optional[BytesIO]:
        file_path = pathlib.Path(self.file_dir) / file_id
        if not file_path.is_file():
            return None
        with open(file_path, 'rb') as file:
            return BytesIO(file.read())

    def _upload(self, file: FileStorage) -> tuple[FileStaticInfo, BytesIO]:
        io = BytesIO()
        file.save(io)
        byte_file = io.getvalue()

        file_hash = hash_file(byte_file)
        if not (self.file_dir / file_hash).exists():
            with (self.file_dir / file_hash).open('wb') as file:
                file.write(data)

        file_info: FileStaticInfo = {
            "file_id": file_hash,
            "file_size": io.tell(),
            "property": {}
        }

        return file_info, io


class FileAPIAccessDrive(FileAPIImpl, FileAPIStorageDrive, FileAPIConfigDrive, ABC):
    def __init__(self, repo_name: str, create_not_exist: bool, access_token: str = None):
        FileAPIStorageDrive.__init__(self, repo_name, create_not_exist)
        FileAPIConfigDrive.__init__(self, repo_name, create_not_exist)
        self.access_token = access_token

    @property
    def repo_exist(self) -> bool:
        return self.config_dir.exists() and self.file_dir.exists()

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

    def upload_repo_file(self, path: str, file: FileStorage) -> tuple[FileSpecialInfo, list[str]]:

        file_static, io = self._upload(file)

        io.close()

        keys = path.lstrip('/').split('/')

        file_info: FileSpecialInfo = {
            "file_id": file_static['file_id'],
            "mimetype": file.mimetype,
            "file_size": file_static['file_size'],
            "last_update": time.time_ns()
        }

        if keys[0]:
            self._set_by_path(self.mapping, keys + [file.filename], file_info)
        else:
            self.mapping.update({file.filename: file_info})

        return file_info, keys

    def list_repo_dir(self, path: str) -> Optional[dict[FileName, FileSpecialInfo]]:
        keys = path.lstrip('/').split('/')

        directory_data = self.mapping

        if keys:
            directory_data = self._get_by_path(self.mapping, keys)

        if not isinstance(directory_data, dict):
            return None

        result = {}
        for key in directory_data:
            data: FileSpecialInfo = directory_data[key]
            try:
                data: FileSpecialInfo = data
                result.update({key: data})
            except TypeMisMatch:
                result.update({key: None if isinstance(data, dict) else {
                    "file_type": "directory"
                }})

        return result

    def next_repo_dir(self, path: Optional[str], d_next: int = None):
        if not d_next:
            dir_lst = self.list_repo_dir(path)
            iter_id = int(str(abs(hash(str(dir_lst)) + hash(path)))[:6])
            iter_id += random.randint(-2000, 1000)
            if len(iter_storage) > 300:
                for _ in range(200):
                    iter_storage.popitem()
            iter_storage.update({iter_id: (iter(dir_lst), dir_lst, len(dir_lst))})
            try:
                key = next(iter_storage[iter_id][0])
                return {key: dir_lst[key]}, len(dir_lst), iter_id
            except StopIteration:
                return None, 0, 0
        else:
            info = None
            try:
                info = iter_storage.pop(d_next)
            except KeyError:
                pass

            if not info:
                return None, 0, -114514

            try:
                dir_iter = info[0]
                lst = info[1]
                length = info[2]

                key = next(dir_iter)
                iter_id = int(str(abs(hash(str(dir_iter) + str(dir_iter)) + hash(path)))[:8])
                iter_id += random.randint(-2000, 1000)
                iter_storage.update({iter_id: (dir_iter, lst, length)})
                return {key: lst[key]}, length, iter_id
            except StopIteration:
                return None, 0, 0

    def quires_repo_file(self, path) -> Optional[FileSpecialInfo]:
        keys = path.split('/')
        try:
            file_info = self._get_by_path(self.mapping, keys)
            try:
                file_info: FileSpecialInfo = file_info
            except TypeMisMatch:
                if isinstance(file_info, dict):
                    return FileSpecialInfo(
                        file_id=None,
                        mimetype='directory',
                        file_size=-1,
                        last_update=-1
                    )
                return None
            return file_info
        except KeyError:
            return None

    def get_file(self, file_info: FileStaticInfo | FileSpecialInfo) -> Optional[BytesIO]:
        return self._queries(file_info['file_id'])

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


class FileAPIPublic(FileAPIAccessDrive):
    public_instance: "FileAPIPublic" = None

    def __new__(cls, *args, **kwargs):
        if cls.public_instance:
            return cls.public_instance

        cls.public_instance = super().__new__(cls, *args, **kwargs)
        return cls.public_instance

    def __init__(self):
        super().__init__(repo_name='Public', create_not_exist=True)

    def can_access_repo(self, access_token) -> bool:
        return True

    def repo_exist(self) -> bool:
        return True


class FileAPIPrivate(FileAPIAccessDrive):
    def __init__(self, repo_id: str, access_token: str = '', create_not_exist=False):
        super().__init__(create_not_exist=create_not_exist, repo_name=repo_id)
        if self.can_access_repo(access_token):
            self.access_token = access_token

    def can_access_repo(self, access_token) -> bool:
        return access_token == self.config['access_token']


class FileDBModelV2:
    class FileDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        file_id = sa.Column(sa.String(128), unique=True)
        property = sa.Column(sa.JSON)
        access_token = sa.Column(sa.Text)

    class DirectoryDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.Text)
        pointer = sa.Column(sa.Integer, sa.ForeignKey('DirectoryDBModel'))
        access_token = sa.Column(sa.Text)
        property = sa.Column(sa.JSON)

    class DisplayDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        list = sa.Column()


class FileDBModelV1:
    class RepoDBModel(database.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        repo_name = sa.Column(sa.Text, unique=True)
        access_token = sa.Column(sa.Text)
        mapping = sa.Column(sa.JSON)


RepoDBModel = FileDBModelV1.RepoDBModel
