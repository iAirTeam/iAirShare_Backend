from __future__ import annotations

import copy
import inspect
import pathlib
import random
import sys

if sys.version_info < (3, 11):  # Support for lower version
    from typing import Optional, Type, Literal, Union, Tuple, List, Dict, Set
    from typing_extensions import TypedDict
else:
    from typing import Optional, TypedDict, Type, Literal, Union, Tuple, List, Dict, Self, Set

from abc import abstractmethod, ABC
from io import BytesIO

from werkzeug.datastructures import FileStorage

from .structure import *


class FileAPIImpl(ABC):

    @abstractmethod
    def upload_repo_file(self, path: Optional[str], file: FileStorage, create_parents=False) -> FileId:
        """
        向 Repo 上传文件
        :param create_parents: 在父目录不存在时, 是否自动创建
        :param path: 目录位置
        :param file: 文件(Flask Werkzeug的FileStorage)
        :return: FileId
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

    @staticmethod
    @abstractmethod
    def get_file(file_info: Optional[FileStaticInfo] | str):
        pass

    @abstractmethod
    def unlink_repo_file(self, path: str) -> bool:
        """
        移除目标 path mapping 链接 (≈删除文件)
        :param path: 文件路径
        :return: 是否成功删除
        """
        pass

    @abstractmethod
    def move_repo_file(self, src_path: str, dest_path: str) -> bool:
        """
        移动目标 old_path 指向的内容到 new_path (≈可以理解为移动文件(夹))
        :param dest_path: 目标位置
        :param src_path: 欲移动文件(夹)位置
        :return: 是否成功移动
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

    def get_file(self, file_info: FileSpecialInfo) -> Optional[BytesIO]:
        """
        通过文件信息获取文件数据
        :param file_info: 文件信息(如FileSpecialInfo)
        :return: 文件数据(BytesIO) 不存在时为 None
        """
        return self._queries(file_info['file_id'])


# noinspection PyUnusedLocal
class FileAPIConfig(ABC):

    def __init__(self, repo_id: str, create_not_exist: bool):
        """
        :param create_not_exist: 当不存在时创建
        :param repo_id: 存储库Id
        """
        pass

    @staticmethod
    def _path_split(path: str):
        return path.strip('/').split('/')

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

    @abstractmethod
    def locate_file(self, path: str) -> Optional[FileBase]:
        pass

    @abstractmethod
    def locate_dir(self, path: str) -> Optional[FileMapping]:
        pass

    @abstractmethod
    def set_file(self, path: str, file: FileBase, create_parents=False):
        pass

    @abstractmethod
    def unset_file(self, path: str):
        pass


class FileAPIDriveBase:
    def __init__(self):
        base_dir = pathlib.Path('instance')
        file_dir = base_dir / 'files'

        self.base_dir: pathlib.Path = pathlib.Path(base_dir)
        self.file_dir: pathlib.Path = pathlib.Path(file_dir)


class FileAPIAccess(FileAPIImpl, FileAPIStorage, FileAPIConfig, ABC):
    def __init__(self, repo_id: str, create_not_exist: bool, access_token: str = None):
        super().__init__(repo_id=repo_id, create_not_exist=create_not_exist)
        self.access_token = access_token

    @property
    def repo_exist(self) -> bool:
        return self.config_dir.exists() and self.file_dir.exists()

    def upload_repo_file(self, path: str, file: FileStorage, create_parents=False) -> FileSpecialInfo:

        file_static, io = self._upload(file)

        io.close()

        file_info: FileSpecialInfo = {
            "file_id": file_static['file_id'],
            "mimetype": file.mimetype,
            "file_size": file_static['file_size'],
            "last_update": time.time()
        }

        self.set_file(path, File(
            file_name=file.filename,
            file_property=file_info,
            pointer=file_static['file_id']
        ), create_parents)

        return file_info

    def list_repo_dir(self, path: str) -> Optional[FileMapping]:
        raw = copy.deepcopy(self.locate_dir(path))

        if not isinstance(raw, set):
            return None

        for file in raw:
            file.pointer = None
            if file.file_type != FileType.directory:
                file.file_property['file_id'] = None

        return raw

    def next_repo_dir(self, path: Optional[str], d_next: int = None):
        if not d_next:
            dir_lst = self.list_repo_dir(path)
            if not dir_lst:
                return None, 0, 0
            iter_id = int(str(abs(hash(str(dir_lst)) + hash(path)))[:6])
            iter_id += random.randint(-2000, 1000)
            if len(iter_storage) > 300:
                for _ in range(200):
                    iter_storage.popitem()
            iter_storage.update({iter_id: (iter(dir_lst), dir_lst, len(dir_lst), path)})
            try:
                data = next(iter_storage[iter_id][0])

                return data, len(dir_lst), iter_id
            except StopIteration | TypeError:
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
                path = info[3]

                data = next(dir_iter)
                iter_id = int(str(abs(hash(str(dir_iter) + str(dir_iter)) + hash(path)))[:8])
                iter_id += random.randint(-2000, 1000)
                iter_storage.update({iter_id: (dir_iter, lst, length, path)})
                return data, length, iter_id
            except StopIteration:
                return None, 0, 0

    def quires_repo_file(self, path) -> Optional[FileBase]:
        try:
            result = copy.deepcopy(self.locate_file(path))
            if not isinstance(result, FileBase):
                return None
            if result.file_type == FileType.file:
                result.pointer = None
            return result
        except KeyError:
            return None

    def get_file(self, file_info: FileStaticInfo | FileSpecialInfo) -> Optional[BytesIO]:
        return self._queries(file_info['file_id'])

    def unlink_repo_file(self, path) -> FileId:
        return self.unset_file(path)

    def move_repo_file(self, source_path: str, dest_path: str) -> bool:
        src_file = self.locate_file(source_path)
        dest_file = self.locate_file(dest_path)
        if src_file and not dest_file:
            self.set_file(dest_path, copy.deepcopy(src_file))
            self.unset_file(source_path)
            return True
        else:
            return False

    def __getattribute__(self, item: str):
        ret_item = super().__getattribute__(item)
        if item in (
                'can_access_repo',
                '_save_storage'
        ):
            return ret_item

        frame = inspect.currentframe()

        if frame.f_back.f_code.co_filename == frame.f_code.co_filename or not callable(ret_item) and \
                not (item.endswith('_dir') and item in (
                        'config',
                        'mapping'
                )):
            return ret_item

        return ret_item if self.can_access_repo(self.access_token) \
            else None
