"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

import re
import uuid as unique_id
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional, Type, TYPE_CHECKING

import dacite.config as dacite_config
import dacite.core as dacite

from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Status
from silex_client.utils.parameter_types import CommandParameterMeta

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

# Alias the metaclass type, to avoid clash with the type attribute
Type = type


@dataclass()
class ParameterBuffer:
    """
    Store the data of a parameter, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing and deserializing this buffer to json
    PRIVATE_FIELDS = []
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["type"]

    #: The type of the parameter, must be a class definition or a CommandParameterMeta instance
    type: Type = field()
    #: Name of the parameter, must have no space or special characters
    name: str = field()
    #: The value that will return the parameter
    value: Any = field(default=None)
    #: The name of the parameter, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: Specify if the parameter must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Specify if the parameter gets its value from a command output or not
    command_output: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="")
    #: A Unique ID to help differentiate multiple actions
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

        # Check if the parameter gets a command output
        if isinstance(self.value, CommandOutput):
            self.command_output = True
            self.hide = True

        # Get the default value from to the type
        if self.value is None and isinstance(self.type, CommandParameterMeta):
            self.value = self.type.get_default()

    def get_value(self, action_query: ActionQuery) -> Any:
        # If the value is the output of an other command, get is
        if self.command_output:
            splited_path = self.value.split(":")

            command_path = splited_path[0]
            if len(command_path) > 1:
                command_path = ":".join(command_path[:2])
            command = action_query.get_command(self.value)

            value = command.output_result if command is not None else None
            if len(command_path) > 2 and isinstance(value, dict):
                value = value.get(command_path[3])
            return value

        # If the value is a callable, call it (for mutable default values)
        if callable(self.value):
            return self.value()

        return self.value

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        result = []

        for f in fields(self):
            if f.name in self.PRIVATE_FIELDS:
                continue

            result.append((f.name, getattr(self, f.name)))

        return dict(result)

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        # Don't take the modifications of the hidden parameters
        if self.hide:
            return

        for private_field in self.PRIVATE_FIELDS + self.READONLY_FIELDS:
            serialized_data[private_field] = getattr(self, private_field)

        config = dacite_config.Config(cast=[Status, CommandOutput])
        new_data = dacite.from_dict(ParameterBuffer, serialized_data, config)

        self.__dict__.update(new_data.__dict__)

    @classmethod
    def construct(cls, serialized_data: Dict[str, Any]) -> ParameterBuffer:
        """
        Create an parameter buffer from serialized data
        """
        config = dacite_config.Config(cast=[Status, CommandOutput])
        parameter = dacite.from_dict(ParameterBuffer, serialized_data, config)

        parameter.deserialize(serialized_data)
        return parameter
