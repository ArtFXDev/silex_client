"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

import re
import uuid as unique_id
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Union, Optional, Type

import dacite

from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Status
from silex_client.utils.parameter_types import CommandParameterMeta

ParameterType = CommandParameterMeta("Parameter", (), {})


@dataclass()
class ParameterBuffer:
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = []

    #: The type of the parameter, must be a class definition or a CommandParameterMeta instance
    type: Union[Type[object], Type[ParameterType]] = field()
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

        dacite_config = dacite.Config(cast=[Status, CommandOutput])
        new_data = dacite.from_dict(ParameterBuffer, serialized_data, dacite_config)

        for private_field in self.PRIVATE_FIELDS:
            setattr(new_data, private_field, getattr(self, private_field))

        self.__dict__.update(new_data.__dict__)
