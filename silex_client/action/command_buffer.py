"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import importlib
import os
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, TypeVar, Union

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_base import CommandBase
from silex_client.action.connection import ConnectionOut, ConnectionIn
from silex_client.action.parameter_buffer import ParameterBuffer
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
    #: Childs in the buffer hierarchy of buffer of the action
    children: Dict[str, ParameterBuffer] = field(default_factory=dict)
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

    def __post_init__(self):
        super().__post_init__()

        # Get the executor
        self.executor = self._get_executor(self.path)

    @property
    def parameters(self) -> Dict[str, ParameterBuffer]:
        """
        Alias for children
        """
        return self.children

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
            parameters = CommandParameters(action_query, self)
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
        parameters = CommandParameters(action_query, self)
        async with RedirectWebsocketLogs(action_query, self) as log:
            await self.executor.setup(parameters, action_query, log)

    @classmethod
    def construct(
        cls, serialized_data: Dict[str, Any], parent: BaseBuffer = None
    ) -> CommandBuffer:
        """
        Create an command buffer from serialized data
        """
        config = dacite_config.Config(cast=[Status, ConnectionOut, ConnectionIn])

        # Initialize the buffer without the children, since the children needs special treatment
        filtered_data = copy.copy(serialized_data)
        filtered_data["parent"] = parent
        for child_type in cls.get_child_types():
            filtered_data.pop(child_type.buffer_type, None)
        command = dacite.from_dict(cls, filtered_data, config)

        # Get the default data from the executor and patch it with the serialized data
        executor_parameters = copy.deepcopy(command.executor.parameters)
        serialized_parameters = serialized_data.get("parameters", {})
        for parameter_name, parameter in executor_parameters.items():
            parameter["name"] = parameter_name

            # The parameters can be defined with <key>=<value> as a shortcut
            if not isinstance(serialized_parameters.get(parameter_name, {}), dict):
                serialized_parameters[parameter_name] = {
                    "input": serialized_parameters[parameter_name]
                }

            # Apply the parameters to the default parameters
            serialized_data["parameters"] = jsondiff.patch(
                executor_parameters, serialized_parameters
            )

        return super().construct(serialized_data, parent)


class CommandParameters:
    """
    Helper to get and set the parameters values of a command quickly
    """

    def __init__(self, action_query: ActionQuery, command: CommandBuffer):
        self.action_query = action_query
        self.command = command

    def __getitem__(self, key: str):
        return self.command.children[key].get_output(self.action_query)

    def __setitem__(self, key: str, value: Any):
        self.command.children[key].input = value

    def get(self, key: str, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value.
        Return the default if the parametr does not exists
        """
        if key not in self.command.children:
            return default
        return self.__getitem__(key)

    def get_raw(self, key, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value without casting it to the expected type
        Return the default if the parametr does not exists
        """
        if key not in self.command.children:
            return default
        return self.command.children[key].input

    def get_buffer(self, key) -> ParameterBuffer:
        """
        Return the parameter buffer directly
        """
        return self.command.children[key]

    def keys(self) -> List[str]:
        """Same method a the original dict"""
        return list(self.command.children.keys())

    def values(self) -> List[Any]:
        """Same method a the original dict"""
        return [
            child.get_output(self.action_query)
            for child in self.command.children.values()
        ]

    def items(self) -> Dict[str, Any]:
        """Same method a the original dict"""
        return {
            name: child.get_output(self.action_query)
            for name, child in self.command.children.items()
        }
