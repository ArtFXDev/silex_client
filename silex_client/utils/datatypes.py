"""
@author: TD gang

Set of class that override basic class like dict
to add specific behaviour
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


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


class CommandOutput(str):
    """
    Helper to differenciate the strings from the command_output
    """

    def get_output_data(self, action_buffer: ActionQuery) -> Any:
        command = action_buffer.get_command(self)
        return command.output_result if command is not None else None
