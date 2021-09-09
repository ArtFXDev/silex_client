from typing import Any


class ReadOnlyError(Exception):
    """
    Simple exception for the readonly datatypes
    """


class ReadOnlyDict(dict):
    """
    Pointer to an editable dict. It allows to read its data but not to edit it
    """
    def __init__(self, target: dict):
        self._target = target

    def __repr__(self) -> str:
        return self._target.__repr__()

    def __str__(self) -> str:
        return self._target.__str__()

    def __getitem__(self, key) -> Any:
        return self._target[key]

    @staticmethod
    def __readonly__(*args, **kwargs) -> None:
        raise ReadOnlyError("This dictionary is readonly")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    clear = __readonly__
    update = __readonly__

    def get(self, key: str, default: Any = None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        return self._target.items()

    def keys(self):
        return self._target.keys()

    def values(self):
        return self._target.values()
