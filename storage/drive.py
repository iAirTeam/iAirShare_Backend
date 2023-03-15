import atexit
import json

from .base import *
from .structure import *

from utils.encrypt import hash_file
from utils.exceptions import *
from utils import serialize

repo_storage: dict["FileAPIConfig"] = {}


class FileAPIConfigDrive(FileAPIDriveBase, FileAPIConfig):

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

    def locate_file(self, path: str, _depth: int = 0, _loc: FileMapping = None) -> Optional[FileBase]:
        key = self._path_split(path)

        if not _loc:
            _loc = self.mapping

        for file in _loc:
            if file.file_name != key[_depth]:
                continue
            if len(key) > (_depth + 1) and file.file_type == FileType.directory:
                return self.locate_file(path, _depth=_depth + 1, _loc=file.pointer)
            return file

    def locate_dir(self, path: str, _depth: int = 0, _loc: FileMapping = None) -> FileMapping:
        key = self._path_split(path)

        if not _loc:
            _loc = self.mapping

        if not key[_depth]:
            return _loc

        for file in _loc:
            if file.file_name != key[_depth]:
                continue
            if len(key) > (_depth + 1) and file.file_type == FileType.directory:
                return self.locate_dir(path, _depth=_depth + 1, _loc=file.pointer)
            if file.file_type == FileType.directory:
                return file.pointer

    def set_folder(self, path: str, directory: Directory):
        return self.set_file(path, file=directory)

    def set_file(self, path: str, file: FileBase, create_parents=False):
        if not file:
            raise InvalidFile
        key = self._path_split(path)
        if len(key) == 1 and not key[0]:
            self._mapping |= {file}
        else:
            return self.set_file_subs(path, file, create_parents)
        return key

    def set_file_subs(self, path: str, file: FileBase, create_parents=False):
        def creation_locate(cur_path: str, creat: FileBase, _depth: int = 0, _loc: FileMapping = None)\
                -> Optional[FileBase]:
            key = self._path_split(cur_path)

            if not _loc:
                _loc = self.mapping

            for cur_file in _loc:
                if cur_file.file_name != key[_depth]:
                    continue
                if len(key) > (_depth + 1) and cur_file.file_type == FileType.directory:
                    return creation_locate(cur_path, creat, _depth=_depth + 1, _loc=cur_file.pointer)
                return cur_file

            tmp_create = Directory(file_name=key[_depth], pointer=set()) if len(key) > (_depth + 1) \
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

    def unset_file(self, path: str):
        key = self._path_split(path)
        tmp = None
        for file in self.locate_file('/'.join(key[:-1])).pointer:
            if file.file_name == [path[-1]]:
                tmp = file
                del file
        return tmp

    def __init__(self, repo_id: str, create_not_exist):
        _pre_inited = True

        if not hasattr(self, '_config'):
            _pre_inited = False
            self._config: RepoConfigAccessStructureRaw = {
                "repo_name": repo_id,
                "mapping": [],
                "permission_nodes": {},
                "access_token": ""
            }

        super().__init__(repo_id=repo_id, create_not_exist=create_not_exist)

        config_dir = self.base_dir / f"{repo_id + '_' if repo_id else ''}config.json"

        if not config_dir.exists() and create_not_exist:
            with config_dir.open('w') as file:
                json.dump(self.config, file)
        elif not config_dir.is_file() and create_not_exist:
            config_dir.unlink(missing_ok=True)
            with config_dir.open('w') as file:
                json.dump(self.config, file)
        elif not _pre_inited:
            try:
                with config_dir.open('r+', encoding='UTF-8') as file:
                    try:
                        self._config: RepoConfigAccessStructure = json.load(file)
                    except ValueError:
                        json.dump(self.config, file)
            except FileNotFoundError:
                pass

        if not _pre_inited and config_dir.exists() and create_not_exist:
            atexit.register(self._save_storage)

        self.config_dir = config_dir

        new_mapping = set()

        for item in self._config['mapping']:
            if not isinstance(item, FileBase):
                item = FileBase(**item)
            new_mapping |= {item}

        self.config['mapping'] = new_mapping

        self._mapping = self.config['mapping']

    def _save_storage(self):
        """
        自动保存函数 (Use save_storage instead, should not be called manually)
        :return: None
        """
        if not self.config_dir.exists():
            return
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
    def config(self) -> RepoConfigAccessStructure:
        return self._config

    @property
    def mapping(self):
        return self._mapping


class FileAPIStorageDrive(FileAPIDriveBase, FileAPIStorage, ABC):
    def __init__(self, repo_id: str, create_not_exist=True):
        super().__init__()

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

    async def _upload(self, file: FileStorage) -> tuple[FileStaticInfo, BytesIO]:
        io = file if isinstance(file, BytesIO) else BytesIO(file.stream.read())
        byte_file = memoryview(io.getvalue())

        file_hash = hash_file(byte_file)
        if not (self.file_dir / file_hash).exists():
            file.stream.seek(0)
            await file.save(self.file_dir / file_hash)

        file_info: FileStaticInfo = {
            "file_id": file_hash,
            "file_size": io.tell(),
            "property": {}
        }

        return file_info, io
