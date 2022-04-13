from abc import ABC, abstractmethod

from typing import TypeVar, Generic

T = TypeVar("T")


class SocketType(ABC, Generic[T]):
    @abstractmethod
    def get_default(self):
        pass

    @abstractmethod
    def cast(self, value) -> T:
        pass

    def rebuild(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
