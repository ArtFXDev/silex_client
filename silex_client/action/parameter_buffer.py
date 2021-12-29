"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, TYPE_CHECKING

from silex_client.action.base_buffer import BaseBuffer 
from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.parameter_types import CommandParameterMeta, AnyParameter

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

# Alias the metaclass type, to avoid clash with the type attribute
Type = type


@dataclass()
class ParameterBuffer(BaseBuffer):
    """
    Store the data of a parameter, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing and deserializing this buffer to json
    PRIVATE_FIELDS = ["outdated_cache", "serialize_cache", "parent"]
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["type", "label"]

    #: The type of the parameter, must be a class definition or a CommandParameterMeta instance
    type: Type = field(default=type(None))
    #: The value that will return the parameter
    value: Any = field(default=None)
    #: Specify if the parameter gets its value from a command output or not
    command_output: bool = field(compare=False, repr=False, default=False)

    def __post_init__(self):
        super().__post_init__()

        # Check if the parameter gets a command output
        if isinstance(self.value, CommandOutput):
            self.command_output = True
            self.hide = True

        # The AnyParameter type does not have any widget in the frontend
        if self.type is AnyParameter:
            self.hide = True

        # Get the default value from to the type
        if self.value is None and isinstance(self.type, CommandParameterMeta):
            self.value = self.type.get_default()

    def get_value(self, action_query: ActionQuery) -> Any:
        """
        Get the value of the parameter, always use this method to get
        the value of a parameter, this will resolve references, callable...
        """
        # If the value is the output of an other command, get is
        if isinstance(self.value, CommandOutput):
            return self.value.get_value(action_query)

        # If the value is a callable, call it (for mutable default values)
        if callable(self.value):
            return self.value()

        return self.value
