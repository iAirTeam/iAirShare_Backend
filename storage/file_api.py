from . import integrated
from .drive import *


class FileAPIPublic(FileAPIAccess, RepoMappingDrive, RepoStorageDrive):
    public_instance: "FileAPIPublic" = None

    def __new__(cls, *args, **kwargs):
        if cls.public_instance:
            return cls.public_instance

        cls.public_instance = super().__new__(cls, *args, **kwargs)
        return cls.public_instance

    def __init__(self):
        super().__init__(repo_id='public', create_not_exist=True)

    def verify_code(self, access_token) -> bool:
        return True

    def repo_exist(self) -> bool:
        return True


class FileAPIPrivate(FileAPIAccess, RepoMappingDrive, RepoStorageDrive):
    def __init__(self, repo_id: str, access_token: str = '', create_not_exist=False):
        self.access_token = access_token
        super().__init__(create_not_exist=create_not_exist, repo_id=repo_id, access_token=access_token)

    def verify_code(self, access_token) -> bool:
        return access_token == self._config['access_token']


class AdminFileAPI(FileAPIPrivate):
    def __init__(self, repo_id: str, token='', default_code='', create_not_exist=False):
        super().__init__(repo_id=repo_id, access_token=default_code, create_not_exist=create_not_exist)
        self.admin_token = token
        self.access_token = default_code

    def verify_code(self, access_token) -> bool:
        return integrated.verify_admin_code(self.admin_token) or super().verify_code(access_token)
