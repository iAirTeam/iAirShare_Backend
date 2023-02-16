import json
import os
import pathlib
import random
from typing import Optional, TypedDict, Self, Type, Literal, Union
from abc import abstractmethod, ABC
from io import BytesIO
import atexit

from werkzeug.datastructures import FileStorage

from .vars import *
from .queries import *
from .exceptions import *
from .encrypt import custom_hash, hash_file

RepoId = str | int
FileId = str | None
RepoFileId = int

iter_storage = {}


class File:
    def __init__(self, file_id: FileId, file_name: str = '[File]'):
        self.file_name = file_name
        self.file_id = file_id

    def __hash__(self):
        return hash(self.file_id)

    def __eq__(self, other):
        if issubclass(other, File):
            return self.file_id == other.file_id
        if isinstance(other, int) or isinstance(other, str):
            return self.file_id == other

        return False


FileInfo = File | Type["FileMapping"]
FileMapping = dict[FileId, FileInfo]


class RepoFile:
    def __init__(self, repo_file_id: RepoFileId, repo: "FileAPIBase" = None):
        self.repo_file_id = repo_file_id
        self.repo = repo

    def __hash__(self):
        return hash(f'{self.repo}#{self.repo_file_id}')

    def __eq__(self, other):
        if issubclass(other, RepoFile):
            return hash(self) == hash(other)
        if isinstance(other, int):
            return self.file_id == other

        return False


class ConfigStructure(TypedDict):
    repo_id: RepoId
    file_mapping: FileMapping


class FileAPIBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def _queries(self, file_id):
        pass

    @abstractmethod
    def quires_repo(self, path: str) -> Union[BytesIO, "IO", "BinaryIO"]:
        pass

    @abstractmethod
    def list_dir(self, path: str) -> iter:
        pass

    @abstractmethod
    def repo_upload(self, path: str, file: FileStorage) -> bytes:
        pass

    @abstractmethod
    def next_dir(self, path: str, d_next: int = None):
        pass


class FileAPIDrive(FileAPIBase):

    def __init__(self, file_suffix=None):
        super().__init__()

        base_dir = pathlib.Path('instance') / ('repo' if not file_suffix else 'repo_' + file_suffix)
        file_dir = base_dir / 'files'

        if not file_dir.exists():
            file_dir.mkdir(parents=True)
        if not (base_dir.is_dir() and file_dir.is_dir()):
            base_dir.unlink()
            file_dir.mkdir(parents=True)

        self.base_dir: pathlib.Path = pathlib.Path(base_dir)
        self.file_dir: pathlib.Path = pathlib.Path(file_dir)

        config_dir = base_dir / 'config.json'

        self.structure = {}

        if not config_dir.exists():
            with config_dir.open('w') as f:
                f.write('{}')
        elif not config_dir.is_file():
            config_dir.unlink(missing_ok=True)
            with config_dir.open('w') as f:
                f.write('{}')
        else:
            with open(config_dir, 'r+', encoding='UTF-8') as f:
                try:
                    self.structure: dict = json.load(f)
                except ValueError:
                    f.write('{}')

        self.config_dir: pathlib.Path = pathlib.Path(config_dir)

        atexit.register(self._save_storage)

    def _save_storage(self):
        with open(self.config_dir, 'w', encoding='UTF-8') as f:
            json.dump(self.structure, f, ensure_ascii=False)

    def _queries(self, file_id):
        file_path = pathlib.Path(self.file_dir) / file_id
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            return BytesIO(f.read())

    @classmethod
    def set_by_path(cls, d, path, val):
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
            return cls.set_by_path(d[key], path, val)

    def repo_upload(self, path: str, file: FileStorage) -> tuple[str, tuple]:
        io = BytesIO()
        file.save(io)
        byte_file = io.getvalue()

        file_hash = hash_file(byte_file)

        with open(self.file_dir / file_hash, 'wb') as f:
            f.write(byte_file)

        keys = path.lstrip('/').split('/')

        if keys[0]:
            self.set_by_path(self.structure, keys + [file.filename], file_hash)
        else:
            self.structure.update({file.filename: file_hash})

        return file_hash, keys

    def list_dir(self, path: str) -> list[str] | None:
        keys = path.lstrip('/').split('/')

        directory_data = self.structure
        if keys:
            self.structure.get(keys)

        if not isinstance(query_data, dict):
            return None

        result = []
        for key, data in directory_data:
            if isinstance(data, str):
                result.append(key)
            elif isinstance(data, dict):
                result.append('[directory]')
            else:
                result.append('[undefined]')

        return result

    def next_dir(self, path: Optional[str], d_next: int = None):
        if not d_next:
            dir_iter = self.list_dir(path)
            iter_id = hash(dir_iter) << (2 << 10) + hash(path) << (2 << 40) + random.randint(10, 8000)
            iter_storage.update({iter_id: (iter(dir_iter), len(dir_iter))})
            return next(iter_storage[iter_id]), len(dir_iter), iter_id
        else:
            dir_iter = None
            try:
                dir_iter = iter_storage.pop(d_next)
            except KeyError:
                pass

            if not dir_iter:
                return None, -114514

            try:
                value = next(dir_iter[0])
                iter_id = hash(dir_iter) << (2 << 10) + hash(path) << (2 << 40) + hash(value)
                iter_storage.update({iter_id: (dir_iter[0], dir_iter[1])})
                return value, dir_iter[1], iter_id
            except StopIteration:
                return None, 0

    def quires_repo(self, path) -> FileId:
        keys = path.split('/')
        try:
            file_id = self.structure.get(*keys)
            if not isinstance(file_id, str):
                return None
            return file_id
        except KeyError:
            return None

    def delete(self, path) -> FileId:
        return self.set_by_path(self.structure, path, None)


class FileAPIPublic(FileAPIDrive):
    public_instance: "FileAPIPublic" = None

    def __new__(cls, *args, **kwargs):
        if cls.public_instance:
            return cls.public_instance

        cls.public_instance = super().__new__(cls, *args, **kwargs)
        return cls.public_instance


class FileAPIPrivateV1(FileAPIDrive, ABC):

    def __init__(self, file_path='file'):
        super().__init__()
        self.file_path = file_path
        ...

    def queries(self, file_hash):
        raise NotImplementedError
