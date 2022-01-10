"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import importlib
import os
import traceback
from contextlib import suppress
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.network.websocket_log import RedirectWebsocketLogs
from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


@dataclass()
class CommandBuffer(BaseBuffer):
    """
    Store the data of a command, it is used as a comunication payload with the UI
    """

    PRIVATE_FIELDS = [
        "output_result",
        "executor",
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]
    READONLY_FIELDS = ["logs", "label"]
    CHILD_NAME = "parameters"
    ALLOW_HIDE_CHILDS = False

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
    #: The output of the command, it can be passed to an other command
    output_result: Any = field(default=None, init=False)
    #: The callable that will be used when the command is executed
    executor: CommandBase = field(init=False)
    #: List of all the logs during the execution of that command
    logs: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        # Get the executor
        self.executor = self._get_executor(self.path)

    @property
    def child_type(self):
        return ParameterBuffer

    @property
    def parameters(self) -> Dict[str, ParameterBuffer]:
        return self.children

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
            key: value.get_value(action_query) for key, value in self.children.items()
        }
        with suppress(TypeError):
            parameters = copy.deepcopy(parameters)

        # Run the executor and copy the parameters
        # to prevent them from being modified during execution
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
        return self.ask_user or not all(
            parameter.value is not None or parameter.hide
            for parameter in self.children.values()
        )

    async def setup(self, action_query: ActionQuery):
        """
        Call the setup of the command, the setup method is used to edit the command attributes
        dynamically (parameters, states...)
        """
        # Create a dictionary that only contains the name and the value of the parameters
        # without infos like the type, label...
        parameters = {
            key: value.get_value(action_query) for key, value in self.children.items()
        }
        with suppress(TypeError):
            parameters = copy.deepcopy(parameters)

        async with RedirectWebsocketLogs(action_query, self) as log:
            await self.executor.setup(parameters, action_query, log)

    @classmethod
    def construct(
        cls, serialized_data: Dict[str, Any], parent: BaseBuffer = None
    ) -> CommandBuffer:
        """
        Create an command buffer from serialized data
        """
        config = dacite_config.Config(cast=[Status, CommandOutput])

        # Initialize the buffer without the children, since the children needs special treatment
        filtered_data = serialized_data
        filtered_data["parent"] = parent
        if cls.CHILD_NAME in serialized_data:
            filtered_data = copy.copy(serialized_data)
            del filtered_data[cls.CHILD_NAME]
        command = dacite.from_dict(cls, filtered_data, config)

        # Get the default data from the executor and patch it with the serialized data
        executor_parameters = copy.deepcopy(command.executor.parameters)
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

        return super().construct(serialized_data, parent)
