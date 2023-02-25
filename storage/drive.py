import copy

from .base import *
from .structure import *


class FileAPIConfigDrive(FileAPIDriveBase, FileAPIConfig):
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

    def set_file(self, path: str, file: FileBase):
        key = self._path_split(path)
        if len(key) == 1:
            self._mapping |= {file}
        else:
            return self.set_file_subs(path, file)
        return key

    def set_file_subs(self, path: str, file: FileBase):
        top_place = self.locate_file(path)
        if not top_place:
            return None
        place = top_place.pointer
        place |= {file}
        return path

    def unset_file(self, path: str, file: FileBase):
        key = self._path_split(path)
        tmp = None
        for file in self.locate_file('/'.join(key[:-1])).pointer:
            if file.file_name == [path[-1]]:
                tmp = file
                del file
        return tmp

    def __init__(self, repo_name: str, create_not_exist=True):
        super().__init__(repo_name=repo_name, create_not_exist=create_not_exist)

        self._config: RepoConfigAccessStructureRaw = {
            "repo_name": repo_name,
            "mapping": [],
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

        new_mapping = set()

        for item in self._config['mapping']:
            new_mapping |= {FileBase(**item)}

        self.config['mapping'] = new_mapping

        self._mapping = self.config['mapping']

    def __del__(self):
        atexit.unregister(self._save_storage)
        self._save_storage()

    def _save_storage(self):
        """
        自动保存函数 (Use save_storage instead, should not be called manually)
        :return: None
        """
        self._config: dict
        self._config['mapping'] = list(self._config['mapping'])
        with self.config_dir.open('w', encoding='UTF-8') as file:
            json.dump(self._config, file, default=lambda obj: obj.__dict__, ensure_ascii=False, indent=4)

    def save_storage(self):
        config_copied = copy.deepcopy(self._config)
        config_copied['mapping'] = list(config_copied['mapping'])
        with self.config_dir.open('w', encoding='UTF-8') as file:
            json.dump(config, file, default=lambda obj: obj.__dict__, ensure_ascii=False, indent=4)

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
    def __init__(self, repo_name: str, create_not_exist=True):
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
