"""
@author: TD gang

Set of class that override basic class like dict
to add specific behaviour
"""

from __future__ import annotations

import copy


class ReadOnlyError(Exception):
    """
    Simple exception for the readonly datatypes
    """

    pass


class ReadOnlyDict(dict):
    """
    Pointer to an editable dict. It allows to read its data but not to edit it
    """

    @staticmethod
    def __readonly__(*args, **kwargs) -> None:
        raise ReadOnlyError("This dictionary is readonly")

    def __copy__(self) -> ReadOnlyDict:
        cls = self.__class__
        return cls(copy.copy(dict(self)))

    def __deepcopy__(self, memo) -> ReadOnlyDict:
        cls = self.__class__
        return cls(copy.deepcopy(dict(self), memo))

    __setitem__ = __readonly__
    __delitem__ = __readonly__
    pop = __readonly__
    clear = __readonly__
    update = __readonly__
