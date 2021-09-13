from typing import Any


class ReadOnlyError(Exception):
    """
    Simple exception for the readonly datatypes
    """


class ReadOnlyDict(dict):
    """
    Pointer to an editable dict. It allows to read its data but not to edit it
    """
    @staticmethod
    def __readonly__(*args, **kwargs) -> None:
        raise ReadOnlyError("This dictionary is readonly")

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    clear = __readonly__
    update = __readonly__
