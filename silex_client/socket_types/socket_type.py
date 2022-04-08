from abc import ABC, abstractmethod


class SocketType(ABC):
    @abstractmethod
    def get_default(self):
        pass

    def rebuild(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)
