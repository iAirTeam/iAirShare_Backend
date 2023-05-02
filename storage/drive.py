import atexit
import json

from .base import *
from .structure import *

from utils.encrypt import hash_file
from utils.exceptions import *
from utils import serialize
from utils.logging import logger

repo_storage: dict["RepoMapping"] = {}


class RepoMappingDrive(DriveBase, RepoMapping):

    # noinspection PyProtectedMember
    def __new__(cls, *args, **kwargs):
        kw_repo = kwargs.get('repo_id', None)
        repo_id = args[0] if len(args) >= 1 else kw_repo
        if repo_id in repo_storage:
            old_obj = repo_storage[repo_id]
            new_obj = super().__new__(cls)
            new_obj._config = old_obj._config
            return new_obj
        elif not repo_id:
            return super().__new__(cls)
        else:
            obj = super().__new__(cls)
            repo_storage.update({repo_id: obj})
            return obj

    def locate_file(
            self, path: tuple[str] | list[str],
            _depth: int = 0,
            _loc: FileMapping = None
    ) \
            -> Optional[FileBase]:
        if not _loc:
            _loc = self.mapping

        if not path:
            return FileBase(file_name='base.(/)', file_type=FileType.directory, pointer=_loc)

        for file in _loc:
            if file.file_name != path[_depth]:
                continue
            if len(path) > (_depth + 1) and file.file_type == FileType.directory:
                return self.locate_file(path, _depth=_depth + 1, _loc=file.pointer)
            return file

    def locate_dir(self, path: tuple[str] | list[str], _depth: int = 0, _loc: FileMapping = None) -> FileMapping:
        if not _loc:
            _loc = self.mapping

        if not path[_depth]:
            return _loc

        for file in _loc:
            if file.file_name != path[_depth]:
                continue
            if len(path) > (_depth + 1) and file.file_type == FileType.directory:
                return self.locate_dir(path, _depth=_depth + 1, _loc=file.pointer)
            if file.file_type == FileType.directory:
                return file.pointer

    def set_folder(self, path: tuple[str] | list[str], directory: Directory):
        return self.set_file(path, file=directory)

    def set_file(self, path: tuple[str] | list[str], file: FileBase, create_parents=False):
        if not file:
            raise InvalidFile
        if len(path) == 1 and not path[0]:
            self._mapping |= {file}
        else:
            return self.set_file_subs(path, file, create_parents)
        return path

    def set_file_subs(self, path: tuple[str] | list[str], file: FileBase, create_parents=False):
        def creation_locate(
                cur_path: tuple[str] | list[str],
                creat: FileBase,
                _depth: int = 0,
                _loc: FileMapping = None
        )\
                -> Optional[FileBase]:
            if not _loc:
                _loc = self.mapping

            for cur_file in _loc:
                if cur_file.file_name != path[_depth]:
                    continue
                if len(path) > (_depth + 1) and cur_file.file_type == FileType.directory:
                    return creation_locate(cur_path, creat, _depth=_depth + 1, _loc=cur_file.pointer)
                return cur_file

            tmp_create = Directory(file_name=path[_depth], pointer=set()) if len(path) > (_depth + 1) \
                else creat

            _loc |= {tmp_create}

            return tmp_create

        if create_parents:
            creation_locate(path, file)
        else:
            top_place = self.locate_file(path)
            if not top_place:
                return None
            place = top_place.pointer
            place |= {file}
        return path

    def unset_file(self, path: tuple[str] | list[str]):
        tmp = None
        for file in self.locate_file(path[:-1]).pointer:
            if file.file_name == [path[-1]]:
                tmp = file
                del file
        return tmp

    def __init__(self, repo_id: str, create_not_exist):
        _pre_inited = True

        if not hasattr(self, '_config'):
            _pre_inited = False
            self._config: RepoConfigStructureRaw = {
                "repo_name": repo_id,
                "mapping": set(),
                "permission_nodes": {},
                "access_token": ""
            }

        super().__init__(repo_id=repo_id, create_not_exist=create_not_exist)

        config_dir = self.base_dir / f"{repo_id + '_' if repo_id else ''}config.json"

        self.config_dir = config_dir

        if not config_dir.exists() and create_not_exist:
            self._save_storage_always()
        elif not config_dir.is_file() and create_not_exist:
            config_dir.unlink(missing_ok=True)
            self._save_storage_always()
        elif not _pre_inited:
            try:
                with config_dir.open('r+', encoding='UTF-8') as file:
                    try:
                        self._config: RepoConfigStructure = json.load(file)
                    except ValueError:
                        json.dump(self.config, file, default=serialize)
            except FileNotFoundError:
                pass

        if not _pre_inited and config_dir.exists() and create_not_exist:
            atexit.register(self._save_storage)

        map_set = set()

        for item in self._config['mapping']:
            if not isinstance(item, FileBase):
                item = FileBase(**item)
            map_set |= {item}

        self._config: RepoConfigStructure

        self._config['mapping']: FileMapping = map_set

        self._mapping: FileMapping = self.config['mapping']

    def _save_storage(self):
        """
        自动保存函数 (Use save_storage instead, should not be called manually)
        :return: None
        """
        if not self.config_dir.exists():
            return
        self._save_storage_always()

    def _save_storage_always(self):
        """
        自动保存函数 Always Safe (Use save_storage instead, should not be called manually)
        :return: None
        """
        with self.config_dir.open('w', encoding='UTF-8') as file:
            json.dump(self._config, file, default=serialize, ensure_ascii=False, indent=4)

    def __del__(self):
        atexit.unregister(self._save_storage)
        self._save_storage()

    # noinspection PyTypedDict
    def save_storage(self):
        self._save_storage()

    @property
    def repo_name(self) -> str:
        return self._config['repo_name']

    @property
    def config(self) -> RepoConfigStructure:
        return self._config

    @property
    def mapping(self):
        return self._mapping


class RepoStorageDrive(DriveBase, RepoStorage, ABC):
    def __init__(self, repo_id: str, create_not_exist=True):
        super().__init__(repo_id=repo_id, create_not_exist=create_not_exist)

        self.access_token: Optional[str] = None

        if not self.file_dir.exists() and create_not_exist:
            self.file_dir.mkdir(parents=True)
        if not self.base_dir.is_dir() and create_not_exist:
            self.base_dir.unlink()
            self.file_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Instance(Base) Directory: {self.base_dir.absolute()}")

    def _quires(self, file_id) -> Optional[BytesIO]:
        file_path = pathlib.Path(self.file_dir) / file_id
        if not file_path.is_file():
            return None
        with open(file_path, 'rb') as file:
            return BytesIO(file.read())

    def _upload(self, file: IO) -> FileStatic:
        bytes_io = BytesIO(file.read())
        byte_file = bytes_io.getvalue()

        file_hash = hash_file(memoryview(byte_file))
        if not (self.file_dir / file_hash).exists():
            with (self.file_dir / file_hash).open('wb') as fp:
                fp.write(byte_file)

        file_info: FileDriveStatic = {
            "file_id": file_hash,
            "file_size": len(byte_file),
            "file_real_path": (self.file_dir / file_hash),
            "property": {}
        }

        bytes_io.close()

        return file_info
