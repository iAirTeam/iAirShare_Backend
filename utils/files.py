import json
import os
import pathlib
from typing import Optional, TypedDict, Self, Type, Literal, Union
from abc import abstractmethod, ABC
from io import BytesIO

from .vars import *
from .queries import *
from .exceptions import *

RepoId = str | int
FileId = int
RepoFileId = int


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
    def quires_repo(self, repo_file: RepoFile) -> Union[BytesIO, "IO", "BinaryIO"]:
        pass

    @abstractmethod
    def get_repo_files(self, repo) -> set:
        pass


class FileAPIDrive(FileAPIBase, ABC):
    def __init__(self, file_suffix=None):
        super().__init__()

        base_dir = pathlib.Path('instance') / ('repo' if not file_suffix else 'repo_' + file_suffix)
        file_dir = base_dir / 'files'

        if not file_dir.exists():
            file_dir.mkdir(parents=True)
        if not file_dir.is_dir():
            file_dir.unlink()
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
                    self.structure = json.load(f)
                except ValueError:
                    f.write('{}')

        self.config_dir: pathlib.Path = pathlib.Path(config_dir)

    def _queries(self, file_id):
        file_path = pathlib.Path(self.base_dir) / file_id
        if not file_path.exists():
            return None
        with open(file_path, 'rb') as f:
            return f.read()


class FileAPIDriveByName(FileAPIDrive, ABC):
    def __init__(self, file_suffix='public'):
        super().__init__(file_suffix=file_suffix)

    def _get_all(self):
        data = {
            "files": [],
            "count": 0
        }

        for file in self.base_dir.iterdir():
            if file.is_file():
                fileinfo = self._filetype(file)
                data["files"].append({
                    "file_name": file.name,
                    "ext_type": fileinfo,
                })
                data["count"] += 1
            else:
                pass

        return data

    # noinspection PyProtectedMember
    def _queries(self, file_id: str):
        super(FileAPIDriveByName, self)._queries(self._file_fullpath(file_id))

    def _file_fullpath(self, filename: str | pathlib.Path) -> Optional[str | pathlib.Path]:
        path = self.base_dir.absolute() / filename  # flag
        return path if path.exists() else None

    @staticmethod
    def _safe_filename(filename: str):
        seps = os.path.sep + os.path.altsep + '/\\$\'\"'
        for sep in seps:
            if sep:
                filename = filename.replace(sep, "_")
        filename.replace('..', '_')

        # on nt a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename.  In
        # this case we prepend an underline
        nt_badname = ("CON", "AUX", "COM1", "COM2", "COM3", "COM4", "LPT1", "LPT2", "LPT3", "PRN", "NUL")
        if (os.name == "nt"
                and filename
                and filename.split(".")[0].upper() in nt_badname):
            filename = f"_{filename}"

        return filename

    @staticmethod
    def _filetype(file: pathlib.Path):

        ext = file.suffix.lower()
        if ext in image_ext:
            return 'image'
        elif ext in video_ext:
            return 'video'
        else:
            return 'other'


class FileAPIPublic(FileAPIDriveByName):
    public_instance: "FileAPIPublic" = None

    def __new__(cls, *args, **kwargs):
        if cls.public_instance:
            return cls.public_instance

        cls.public_instance = super().__new__(cls, *args, **kwargs)
        return cls.public_instance

    def quires_repo(self, repo_file_id: str):
        file = super()._file_fullpath(repo_file_id)
        if not file:
            return None

        return open(file, 'rb')

    # noinspection PyProtectedMember
    def get_repo_files(self, repo=None):
        if not repo:
            return super()._get_all()
        else:
            raise NoSuchRepoError("Undefined Behavior in Public Repo")


class FileAPIPrivateV1(FileAPIDrive, ABC):

    def __init__(self, file_path='file'):
        super().__init__()
        self.file_path = file_path
        ...

    def queries(self, file_hash):
        raise NotImplementedError
