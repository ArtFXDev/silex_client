from __future__ import annotations
import copy
import importlib
import re
import uuid
from typing import Union
from dataclasses import dataclass, field

from silex_client.utils.log import logger
from silex_client.utils.enums import Status
from silex_client.action.command_base import CommandBase


@dataclass()
class CommandBuffer():
    """
    Store the data of a command
    """
    path: str = field()
    name: Union[str, None] = field(default=None)
    label: Union[str, None] = field(compare=False, repr=False, default=None)
    hide: bool = field(compare=False, repr=False, default=False)
    tooltip: str = field(compare=False, repr=False, default="")
    parameters: dict = field(compare=False, repr=False, default_factory=dict)

    uid: uuid.UUID = field(default_factory=uuid.uuid1, init=False)
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
        for name, value in command_parameters.items():
            if name in self.parameters:
                value["value"] = self.parameters[name]
            # If the value is a callable, call it (for mutable default values)
            if callable(value["value"]):
                value["value"] = value["value"]()
        self.parameters = command_parameters

    def __call__(self, variables):
        # Only run the command if it is valid
        if self.status is Status.INVALID:
            logger.error("Skipping command %s because the buffer is invalid",
                         self.name)
            return
        # Create a shortened version of the parameters and pass them to the executor
        parameters = {
            key: value.get("value", None)
            for key, value in self.parameters.items()
        }
        # Run the executor
        self.executor(parameters, variables)

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
            else:
                raise ImportError
        except (ImportError, AttributeError):
            logger.error("Invalid command path, skipping %s", path)
            self.status = Status.INVALID

        return CommandBase(self)
