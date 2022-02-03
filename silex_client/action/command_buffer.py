"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import importlib
from functools import partial
import os
import traceback
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Dict, List, TypeVar, Union, Tuple, Type

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_base import CommandBase
from silex_client.action.connection import Connection
from silex_client.action.io_buffer import IOBuffer, InputBuffer, OutputBuffer
from silex_client.network.websocket_log import RedirectWebsocketLogs
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

GenericType = TypeVar("GenericType")


@dataclass()
class CommandBuffer(BaseBuffer):
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    PRIVATE_FIELDS = [
        "executor",
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]
    READONLY_FIELDS = ["logs", "label"]
    ALLOW_HIDE_CHILDS = False

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="commands")
    #: The path to the command's module
    path: str = field(default="")
    #: Specify if the parameters must be displayed by the UI or not
    hide_parameters: bool = field(compare=False, repr=False, default=False)
    #: Specify if the command should be asking to the UI a feedback
    ask_user: bool = field(compare=False, repr=False, default=False)
    #: The status of the command, to keep track of the progression, specify the errors
    status: Status = field(default=Status.INITIALIZED, init=False)
    #: The callable that will be used when the command is executed
    executor: CommandBase = field(init=False)
    #: List of all the logs during the execution of that command
    logs: List[Dict[str, str]] = field(default_factory=list)
    #: In the case of a command, the input is not a connection
    input: Dict[str, InputBuffer] = field(default_factory=dict, init=False)
    #: In the case of a command, the output is not a connection
    output: Dict[str, OutputBuffer] = field(default_factory=dict, init=False)

    def __post_init__(self):
        super().__post_init__()

        # Get the executor
        self.executor = self._get_executor(self.path)

    def _get_executor(self, path: str) -> CommandBase:
        """
        Try to import the module and get the Command object
        """
        try:
            split_path = path.split(".")
            module_path = ".".join(split_path[:-1])
            class_name = split_path[-1]

            # Import the module
            module = importlib.import_module(module_path)
            importlib.reload(module)

            # Get the command class
            executor = getattr(module, class_name)

            if issubclass(executor, CommandBase):
                return executor(self)

            # If the module is not a subclass or CommandBase, return an error
            raise ImportError("The given command does not inherit from CommandBase")
        except (ImportError, AttributeError, ModuleNotFoundError) as exception:
            logger.error("Invalid command path, skipping %s (%s)", path, exception)
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
        if self.skip_execution():
            logger.debug("Skipping command %s", self.name)
        else:
            parameters = CommandInput(action_query, self)
            logger.debug("Executing command %s", self.name)
            async with RedirectWebsocketLogs(action_query, self) as log:
                # Set the status to processing
                self.status = Status.PROCESSING

                # Call the actual command
                if execution_type == Execution.FORWARD:
                    await self.executor(parameters, action_query, log)
                elif execution_type == Execution.BACKWARD:
                    await self.executor.undo(parameters, action_query, log)

        # Keep the error statuses
        if self.status in [Status.INVALID, Status.ERROR]:
            return
        # Set the status to completed or initialized according to the execution
        if execution_type == Execution.FORWARD:
            self.status = Status.COMPLETED
        elif execution_type == Execution.BACKWARD:
            self.status = Status.INITIALIZED

    def require_prompt(self) -> bool:
        """
        Check if this command require a user input, by testing the ask_user field
        and none values on the parameters
        """
        if self.skip:
            return False
        if self.ask_user:
            return True
        if all(
            parameter.input is not None or parameter.hide
            for parameter in self.children.values()
        ):
            return False
        return True

    async def setup(self, action_query: ActionQuery):
        """
        Call the setup of the command, the setup method is used to edit the command attributes
        dynamically (parameters, states...)
        """
        parameters = CommandInput(action_query, self)
        async with RedirectWebsocketLogs(action_query, self) as log:
            await self.executor.setup(parameters, action_query, log)

    def serialize(self, ignore_fields: List[str] = None) -> Dict[str, Any]:
        """
        Convert the buffer's data into json so it can be sent to the UI
        """
        if not self.outdated_caches:
            return self.serialize_cache

        if ignore_fields is None:
            ignore_fields = self.PRIVATE_FIELDS

        result = []

        for buffer_field in fields(self):
            if buffer_field.name in ignore_fields:
                continue
            if buffer_field.name in [
                io_type.buffer_type for io_type in self.get_child_types()
            ]:
                children = getattr(self, buffer_field.name)
                children_value = {}
                for child_name, child in children.items():
                    if self.ALLOW_HIDE_CHILDS and child.hide:
                        continue
                    children_value[child_name] = child.serialize()
                result.append((buffer_field.name, children_value))
                continue

            result.append((buffer_field.name, getattr(self, buffer_field.name)))

        self.serialize_cache = copy.deepcopy(dict(result))
        self.outdated_cache = False
        return self.serialize_cache

    @classmethod
    def get_child_types(cls) -> List[Type[IOBuffer]]:
        """
        The childs type are the possible classes that this buffer can have as children
        """
        return [InputBuffer, OutputBuffer]

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        # Don't take the modifications of the hidden commands
        if self.hide and not force:
            return

        current_buffer_data = self.serialize()
        for io_type in self.get_child_types():
            serialized_data.setdefault(io_type.buffer_type, {})

            # If a io update some existing io, it inherit from its buffer type
            for io_name, io_data in serialized_data[io_type.buffer_type].items():
                io_data["name"] = io_name
                current_io_data = current_buffer_data.get(io_type.buffer_type, {})
                existing_io_data = current_io_data.get(io_name)
                if existing_io_data is not None:
                    io_data["buffer_type"] = existing_io_data["buffer_type"]

        # Patch the current buffer's data
        serialized_data = jsondiff.patch(current_buffer_data, serialized_data)

        # Setup dacite to use our deserialize function has a type_hook to create the children
        config_data: Dict[str, Union[list, dict]] = {"cast": [Status, Connection]}
        if BaseBuffer not in self.get_child_types():
            config_data["type_hooks"] = {
                child_type: partial(self._deserialize_child, child_type)
                for child_type in self.get_child_types()
            }
        config = dacite_config.Config(**config_data)

        # Create a new buffer with the patched serialized data
        new_buffer = dacite.from_dict(type(self), serialized_data, config)

        # Keep the current value for the private and readonly fields
        for private_field in self.PRIVATE_FIELDS + self.READONLY_FIELDS:
            setattr(new_buffer, private_field, getattr(self, private_field))

        # Update the current fields value with the new buffer's values
        new_buffer_data = new_buffer.__dict__
        for io_type in self.get_child_types():
            getattr(self, io_type.buffer_type).update(
                new_buffer_data[io_type.buffer_type]
            )
            del new_buffer_data[io_type.buffer_type]
        self.__dict__.update(new_buffer_data)

        self.outdated_cache = True

    @classmethod
    def construct(
        cls, serialized_data: Dict[str, Any], parent: BaseBuffer = None
    ) -> CommandBuffer:
        """
        Create an command buffer from serialized data
        """
        config = dacite_config.Config(cast=[Status, Connection])

        # Initialize the buffer without the children, since the children needs special treatment
        filtered_data = copy.copy(serialized_data)
        filtered_data["parent"] = parent
        for io_type in cls.get_child_types():
            filtered_data.pop(io_type.buffer_type, None)
        command = dacite.from_dict(cls, filtered_data, config)

        # Get the default data from the executor and patch it with the serialized data
        executor_parameters = copy.deepcopy(command.executor.parameters)
        serialized_parameters = serialized_data.get("input", {})
        for parameter_name, parameter in executor_parameters.items():
            parameter["name"] = parameter_name

            # The parameters can be defined with <key>=<value> as a shortcut
            if not isinstance(serialized_parameters.get(parameter_name, {}), dict):
                serialized_parameters[parameter_name] = {
                    "input": serialized_parameters[parameter_name]
                }

            # Apply the parameters to the default parameters
            serialized_data["input"] = jsondiff.patch(
                executor_parameters, serialized_parameters
            )

        return super().construct(serialized_data, parent)

    def get_input(self, action_query: ActionQuery, key: str) -> Any:
        """
        Always use this method to get the input of the buffer
        Return the input after resolving connections
        """
        return self.input[key].get_output(action_query)

    def get_output(self, action_query: ActionQuery, key: str) -> Any:
        """
        Since command's input and outputs are
        """
        return self.output[key].get_output(action_query)


class CommandIO:
    """
    Helper to get and set the parameters values of a command quickly
    """

    def __init__(
        self,
        action_query: ActionQuery,
        command: CommandBuffer,
        data: Dict[str, IOBuffer],
    ):
        self.action_query = action_query
        self.command = command
        self.data = data

    def __getitem__(self, key: str):
        return self.data[key].get_output(self.action_query)

    def __setitem__(self, key: str, value: Any):
        self.data[key].input = value

    def get(self, key: str, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value.
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default
        return self.__getitem__(key)

    def get_raw(self, key, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value without casting it to the expected type
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default
        return self.data[key].input

    def get_buffer(self, key) -> IOBuffer:
        """
        Return the parameter buffer directly
        """
        return self.data[key]

    def keys(self) -> List[str]:
        """Same method a the original dict"""
        return list(self.data.keys())

    def values(self) -> List[Any]:
        """Same method a the original dict"""
        return [child.get_output(self.action_query) for child in self.data.values()]

    def items(self) -> List[Tuple[str, Any]]:
        """Same method a the original dict"""
        return [
            (key, value.get_output(self.action_query))
            for key, value in self.data.items()
        ]

    def update(self, values: Union[CommandIO, Dict[str, Any]]):
        """Update the values with the given dict"""
        for key, value in values.items():
            self[key] = value


class CommandInput(CommandIO):
    def __init__(self, action_query: ActionQuery, command: CommandBuffer):
        self.action_query = action_query
        self.command = command
        self.data = command.input


class CommandOutput(CommandIO):
    def __init__(self, action_query: ActionQuery, command: CommandBuffer):
        self.action_query = action_query
        self.command = command
        self.data = command.output
