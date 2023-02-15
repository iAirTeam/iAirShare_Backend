from abc import ABC, abstractmethod


class QueriesBase(ABC):
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def lookup_user(self, user_id):
        pass
