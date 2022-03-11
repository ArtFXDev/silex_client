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


class SharedVariable:
    """
    Simple container for a variable to share the value between threads without any
    thread safety overhead
    """

    def __init__(self, value):
        self.value = value


class CommandOutput(str):
    """
    Helper to differenciate the strings from the command_output
    """

    def __init__(self, *args, **kwargs):
        super().__init__()

        splited_path = self.split(":")

        # Initialize attrubutes
        self.step = None
        self.command = splited_path[0]
        self.output_keys = []

        # If the user specified more that just the command name
        if len(splited_path) > 1:
            # Get the step and the command
            self.command = splited_path[1]
            self.step = splited_path[0]
            # The output keys are in case the command returns a dict
            # The user can get a particular value in the dict
            for key in splited_path[2:]:
                self.output_keys.append(key)

    def get_command_path(self):
        """
        Get the path to get the command with the method ActionQuery::get_command
        """
        if self.step is not None:
            return f"{self.step}:{self.command}"

        return self.command

    def rebuild(self) -> CommandOutput:
        """
        Since strings a immutable, when modifying the step or command attrubutes
        We need to rebuild entirely the string.

        TODO: Recreate a class that contains a string instead of inheriting from it,
        we let this for now to keep string features like json serialisability,
        but it is not ideal
        """
        return CommandOutput(":".join([self.get_command_path(), *self.output_keys]))

    def get_value(self, action_query: ActionQuery) -> Any:
        """
        Get the actual returned value of the command this path is pointing to
        """
        command = action_query.get_command(self.get_command_path())
        value = command.output_result if command is not None else None

        for key in self.output_keys:
            if isinstance(value, dict):
                value = value.get(key, {})

        # Handle list of CommandOutputs
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, CommandOutput):
                    value[index] = item.get_value(action_query)

        # Handle dict of CommandOutputs
        if isinstance(value, dict):
            for key, item in enumerate(value.items()):
                if isinstance(item, CommandOutput):
                    value[key] = item.get_value(action_query)
                if isinstance(key, CommandOutput):
                    value[key.get_value(action_query)] = value.pop(key)

        if isinstance(value, CommandOutput):
            value = value.get_value(action_query)

        return value
