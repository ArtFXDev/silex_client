"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import importlib
import os
import re
import traceback
import uuid as unique_id
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Dict, Optional, List

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


@dataclass()
class CommandBuffer:
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = ["output_result", "executor", "input_path"]
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["logs"]

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
    parameters: Dict[str, ParameterBuffer] = field(default_factory=dict)
    #: A Unique ID to help differentiate multiple actions
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))
    #: The status of the command, to keep track of the progression, specify the errors
    status: Status = field(default=Status.INITIALIZED, init=False)
    #: The output of the command, it can be passed to an other command
    output_result: Any = field(default=None, init=False)
    #: The input of the command, a path following the schema <step>:<command>
    input_path: CommandOutput = field(default=CommandOutput(""))
    #: The callable that will be used when the command is executed
    executor: CommandBase = field(init=False)
    #: Name of the command, must have no space or special characters
    logs: List[Dict[str, str]] = field(default_factory=list)

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

    def _get_executor(self, path: str) -> CommandBase:
        """
        Try to import the module and get the Command object
        """
        try:
            split_path = path.split(".")
            module = importlib.import_module(".".join(split_path[:-1]))
            importlib.reload(module)
            executor = getattr(module, split_path[-1])
            if issubclass(executor, CommandBase):
                return executor(self)

            # If the module is not a subclass or CommandBase, return an error
            raise ImportError
        except (ImportError, AttributeError) as exception:
            logger.error("Invalid command path, skipping %s", path)
            self.status = Status.INVALID
            if os.getenv("SILEX_LOG_LEVEL") == "DEBUG":
                traceback.print_tb(exception.__traceback__)

            return CommandBase(self)

    async def execute(
        self, action_query: ActionQuery, execution_type: Execution = Execution.FORWARD
    ):
        """
        Execute the command using the executor
        """
        # Create a dictionary that only contains the name and the value of the parameters
        # without infos like the type, label...
        parameters = {
            key: value.get_value(action_query) for key, value in self.parameters.items()
        }

        # Get the input result
        input_value = None
        if self.input_path:
            input_command = action_query.get_command(self.input_path)
            input_value = (
                input_command.output_result if input_command is not None else None
            )

        # Run the executor and copy the parameters
        # to prevent them from being modified during execution
        logger.debug("Executing command %s", self.name)
        if execution_type == Execution.FORWARD:
            await self.executor(input_value, copy.deepcopy(parameters), action_query)
        elif execution_type == Execution.BACKWARD:
            await self.executor.undo(
                input_value, copy.deepcopy(parameters), action_query
            )

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        result = []

        for f in fields(self):
            if f.name == "parameters":
                parameters = getattr(self, f.name)
                parameters_value = {}
                for parameter_name, parameter in parameters.items():
                    parameters_value[parameter_name] = parameter.serialize()
                result.append((f.name, parameters_value))
                continue
            elif f.name in self.PRIVATE_FIELDS:
                continue

            result.append((f.name, getattr(self, f.name)))

        return dict(result)

    def _deserialize_parameters(self, parameter_data: Any) -> Any:
        parameter_name = parameter_data.get("name")
        parameter = self.parameters.get(parameter_name)

        if parameter is None:
            return ParameterBuffer.construct(parameter_data)

        parameter.deserialize(parameter_data)
        return parameter

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        """
        Convert back the action's data from json into this object
        """
        # Don't take the modifications of the hidden commands
        if self.hide and not force:
            return

        # Format the parameters corectly
        executor_parameters = copy.deepcopy(self.executor.parameters)
        serialized_parameters = serialized_data.get("parameters", {})
        for parameter_name, parameter in executor_parameters.items():
            parameter["name"] = parameter_name

            # The parameters can be defined with <key>=<value> as a shortcut
            if not isinstance(serialized_parameters.get(parameter_name, {}), dict):
                serialized_parameters[parameter_name] = {
                    "value": serialized_parameters[parameter_name]
                }

            # Apply the parameters to the default parameters
            serialized_data["parameters"] = jsondiff.patch(
                executor_parameters, serialized_parameters
            )

        config = dacite_config.Config(
            cast=[Status, CommandOutput],
            type_hooks={ParameterBuffer: self._deserialize_parameters},
        )
        new_data = dacite.from_dict(CommandBuffer, serialized_data, config)

        for private_field in self.PRIVATE_FIELDS + self.READONLY_FIELDS:
            setattr(new_data, private_field, getattr(self, private_field))

        self.__dict__.update(new_data.__dict__)

    @classmethod
    def construct(cls, serialized_data: Dict[str, Any]) -> CommandBuffer:
        """
        Create an command buffer from serialized data
        """
        config = dacite_config.Config(cast=[Status, CommandOutput])
        if "parameters" in serialized_data:
            filtered_data = copy.deepcopy(serialized_data)
            del filtered_data["parameters"]
            command = dacite.from_dict(CommandBuffer, filtered_data, config)
        else:
            command = dacite.from_dict(CommandBuffer, serialized_data, config)

        command.deserialize(serialized_data, force=True)
        return command

    def require_prompt(self) -> bool:
        return self.ask_user or not all(
            parameter.value is not None for parameter in self.parameters.values()
        )
