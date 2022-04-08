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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
    #: Defines if the command must be executed or not
    skip: bool = field(default=False)
    #: The progress is only infomational, it should go from 0 to 100
    progress: Optional[int] = field(default=None)

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
        except (
            ImportError,
            AttributeError,
            ModuleNotFoundError,
        ) as exception:
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
        if self.skip:
            logger.debug("Skipping command %s", self.name)
        else:
            # Create a dictionary that only contains the name and the value of the parameters
            # without infos like the type, label...
            parameters = {
                key: value.get_value(action_query)
                for key, value in self.children.items()
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
