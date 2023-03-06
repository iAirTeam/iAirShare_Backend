from . import integrated
from .drive import *

class FileAPIPublic(FileAPIAccess, FileAPIConfigDrive, FileAPIStorageDrive):
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


class FileAPIPrivate(FileAPIAccess, FileAPIConfigDrive, FileAPIStorageDrive):
    def __init__(self, repo_name: str, access_token: str = '', create_not_exist=False):
        super().__init__(create_not_exist=create_not_exist, repo_name=repo_name)
        self.access_token = access_token

    def can_access_repo(self, access_token) -> bool:
        return access_token == self._config['access_token']


class AdminFileAPI(FileAPIPrivate):
    def __init__(self, repo_id: str, token='', create_not_exist=False):
        super().__init__(create_not_exist=create_not_exist, repo_name=repo_id)
        self.access_token = token

    def can_access_repo(self, access_token) -> bool:
        return integrated.verify_admin_code(access_token)
