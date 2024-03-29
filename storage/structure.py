import datetime
import pathlib
import sys
from enum import Enum

from strongtyping.strong_typing import match_class_typing

if sys.version_info < (3, 11):  # pragma: no cover
    from typing import Optional, Type, Union
    from typing_extensions import TypedDict
else:
    from typing import Optional, TypedDict, Type, Union

from typing_extensions import NotRequired

RepoId = str
FileId = str
FileName = str

iter_storage = {}


class FileType(str, Enum):
    file: str = 'file'
    directory: str = 'directory'


class FileSpecialMeta(TypedDict):
    file_id: FileId
    mimetype: NotRequired[str]
    file_size: NotRequired[int]
    last_update: float | datetime.datetime


class FileBase:
    file_type = FileType.file

    def __init__(self,
                 file_name: str,
                 pointer: Union[FileId, "FileMapping"],
                 file_type=file_type,
                 file_property: Optional[FileSpecialMeta] = None
                 ):

        if file_property is None and file_type != FileType.directory:
            file_property = FileSpecialMeta(file_id=pointer, last_update=datetime.datetime.utcnow())
        elif file_property and not file_property.get('last_update') \
                and file_type != FileType.directory:
            file_property['last_update'] = \
                datetime.datetime.fromtimestamp(file_property['last_update'])
        self.file_name: str = file_name
        self.file_type: FileType = file_type
        self.pointer: Union[FileId, "FileMapping"] = pointer
        if isinstance(self.pointer, list):
            proc: FileMapping = set()
            for file in self.pointer:
                proc |= {FileBase(**file)}
            self.pointer = proc
        self.file_property: Optional[FileSpecialMeta] = file_property
        if self.file_type != FileType.directory:
            if not file_property:
                self.file_property: FileSpecialMeta = file_property

            assert self.file_property.get('file_id', self.pointer) == self.pointer, \
                f"{self.file_property['file_id']} != {self.pointer}" \
                f"The property file_id should be same as the pointer!"

            self.file_property['file_id'] = pointer

    def __repr__(self):
        try:
            return f"[{'D' if self.file_type == FileType.directory else 'F'}] {self.file_name}"
        except AttributeError:
            return f"![{'D' if self.file_type == FileType.directory else 'F'}] {id(self)}"

    def __hash__(self):
        if self.file_name is None or self.file_type is None:
            return 0
        tmp_hash = hash(self.file_name) + hash(self.file_type)
        return tmp_hash

    def __eq__(self, other):
        if self.__hash__() == other.__hash__():
            return True
        else:
            return False


class File(FileBase):
    file_type = FileType.file

    def __init__(self,
                 file_name: str,
                 pointer: FileId,
                 file_property: Optional[FileSpecialMeta] = None
                 ):
        super().__init__(file_name, pointer, self.file_type, file_property)


class Directory(FileBase):
    file_type = FileType.directory

    def __init__(self,
                 file_name: str,
                 pointer: "FileMapping" = None
                 ):
        if pointer is None:
            pointer = set()
        super().__init__(file_name, pointer, self.file_type, None)


class FileStatic(TypedDict):
    file_id: FileId
    file_size: int
    property: "FileStaticProperty"


class FileDriveStatic(FileStatic):
    file_real_path: str | pathlib.Path


class FileStaticProperty(TypedDict, total=False):
    detected_file_type: Optional[str]
    i_width: int
    i_height: int
    v_fps_avg: int
    v_bitrate: int
    v_a_bitrate: int
    av_length_sec: float
    prop_ver: int


class FileBaseDict(TypedDict):
    file_name: str
    file_type: str
    file_property: dict
    pointer: "RawFileMapping"


FileMapping = set[FileBase] | list[FileBase]
RawFileMapping = set[FileBaseDict] | list[FileBaseDict]


@match_class_typing
class RepoConfigStructureRaw(TypedDict):
    repo_name: str
    permission_nodes: dict
    access_token: str
    mapping: "RawFileMapping"


@match_class_typing
class RepoConfigStructure(TypedDict):
    repo_name: str
    permission_nodes: dict[str, bool | Type["permission_nodes"]]
    access_token: str
    mapping: "FileMapping"
