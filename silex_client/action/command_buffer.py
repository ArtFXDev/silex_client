"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import importlib
import re
import uuid as unique_id
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Union, Optional

import dacite
import jsondiff

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.enums import Status
from silex_client.utils.log import logger


@dataclass()
class CommandBuffer:
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = ["output_result", "executor"]

    #: The path to the command's module
    path: str = field()
    #: Name of the command, must have no space or special characters
    name: Optional[str] = field(default=None)
    #: The name of the command, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: Specify if the command must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Specify if the parameters must be displayed by the UI or not
    hide_parameters: bool = field(compare=False, repr=False, default=False)
    #: Specify if the command should be asking to the UI a feedback
    ask_user: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="")
    #: Dict that represent the parameters of the command, their type, value, name...
    parameters: Union[CommandParameters, dict] = field(default_factory=dict)
    #: A Unique ID to help differentiate multiple actions
    uuid: str = field(default_factory=lambda: str(unique_id.uuid1()))
    #: The status of the command, to keep track of the progression, specify the errors
    status: Status = field(default=Status.INITIALIZED, init=False)
    #: The output of the command, it can be passed to an other command
    output_result: Any = field(default=None, init=False)
    #: The input of the command, a path following the schema <step>:<command>
    input_path: str = field(default="")
    #: The callable that will be used when the command is executed
    executor: CommandBase = field(init=False)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command name
        if self.name is None:
            self.name = slugify_pattern.sub("_", self.path)
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

        # Get the executor
        self.executor = self._get_executor(self.path)

        # Get the executor's parameter attributes and override them with the given ones
        command_parameters = copy.deepcopy(self.executor.conformed_parameters)
        for value in command_parameters.values():
            # If the value is a callable, call it (for mutable default values)
            if callable(value["value"]):
                value["value"] = value["value"]()

        # The formatting of the parameters can be different, it can be:
        # {<parameter_name>: <parameter_value>} or {<parameter_name>: {"value": <parameter_value>}}
        # We must make sure it follows the format {<parameter_name>: {"value": <parameter_value>}}
        if all(
            not isinstance(value, dict) or "value" not in value.keys()
            for value in self.parameters.values()
        ):
            self.parameters = {
                key: {"value": value} for key, value in self.parameters.items()
            }
        # Apply the parameters to the default parameters
        self.parameters = jsondiff.patch(command_parameters, self.parameters)

    def _get_executor(self, path: str) -> CommandBase:
        """
        Try to import the module and get the Command object
        """
        try:
            split_path = path.split(".")
            module = importlib.import_module(".".join(split_path[:-1]))
            executor = getattr(module, split_path[-1])
            if issubclass(executor, CommandBase):
                return executor(self)

            # If the module is not a subclass or CommandBase, return an error
            raise ImportError
        except (ImportError, AttributeError):
            logger.error("Invalid command path, skipping %s", path)
            self.status = Status.INVALID

            return CommandBase(self)

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        result = []

        for f in fields(self):
            if f.name in self.PRIVATE_FIELDS:
                continue
            else:
                result.append((f.name, getattr(self, f.name)))

        return dict(result)

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        dacite_config = dacite.Config(cast=[Status])
        new_data = dacite.from_dict(CommandBuffer, serialized_data, dacite_config)

        for private_field in self.PRIVATE_FIELDS:
            setattr(new_data, private_field, getattr(self, private_field))

        self.__dict__.update(new_data.__dict__)
