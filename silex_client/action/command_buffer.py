from __future__ import annotations

import copy
import importlib
import re
import uuid as unique_id
from dataclasses import asdict, dataclass, field
from typing import Union, Dict, Any, TYPE_CHECKING

import dacite
import jsondiff

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_base import CommandParameters


@dataclass()
class CommandBuffer:
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    #: The path to the command's module
    path: str = field()
    #: Name of the command, must have no space or special characters
    name: Union[str, None] = field(default=None)
    #: The name of the command, meant to be displayed
    label: Union[str, None] = field(compare=False, repr=False, default=None)
    #: Specify if the command must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="")
    #: Dict that represent the parameters of the command, their type, value, name...
    parameters: CommandParameters = field(default_factory=dict)
    #: A Unique ID to help differentiate multiple actions
    uuid: unique_id.UUID = field(default_factory=unique_id.uuid1, init=False)
    #: The status of the command, to keep track of the progression, specify the errors
    status: Status = field(default=Status.INITIALIZED, init=False)

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
        command_parameters = copy.deepcopy(self.executor.parameters)
        for value in command_parameters.values():
            # If the value is a callable, call it (for mutable default values)
            if callable(value["value"]):
                value["value"] = value["value"]()

        # The formatting of the parameters can be different, it can be:
        # {<parameter_name>: <parameter_value>} or {<parameter_name>: {"value": <parameter_value>}}
        # We need to make sure it follows the format {<parameter_name>: {"value": <parameter_value>}}
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

            self.status = Status.INVALID
            return CommandBase(self)

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        return asdict(self)

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        new_data = dacite.from_dict(CommandBuffer, serialized_data)
        self.__dict__ = new_data.__dict__
