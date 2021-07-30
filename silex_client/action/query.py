from __future__ import annotations
import importlib
import typing
from typing import Union

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection
    from silex_client.utils.config import ActionConfig


class ActionQuery():
    """
    Initialize and execute a given action
    """
    def __init__(self, name: str, ws_connection: WebsocketConnection,
                 config: ActionConfig, **kwargs: dict):
        self.action_name = name
        self.config = config
        self.buffer = ActionBuffer(name, ws_connection)
        self.environment = kwargs

        self._initialize_buffer()

    def execute(self) -> ActionBuffer:
        """
        Execute the action's commands in order,
        send and receive the buffer to the UI when nessesary
        """
        for command in self.buffer:
            command(**self.buffer.variables)

        return self.buffer

    def _initialize_buffer(self) -> None:
        """
        Initialize the buffer from the config
        """
        resolved_action = self.config.resolve_action(self.action_name,
                                                     **self.environment)

        if self.action_name not in resolved_action:
            logger.error("Invalid resolved action")
            return

        action_commands = resolved_action[self.action_name]
        self.buffer.commands = action_commands

    def _run_command(self, command: str, args: Union[list, dict,
                                                     tuple]) -> None:
        """
        Import the modules nessesary to the given command and run it
        """
        # Import the command
        split_module = command.split(".")
        try:
            command_module = importlib.import_module(
                command.replace("." + split_module[-1], ""))
        except ImportError:
            logger.error("Command %s not found", command)
            return

        command_attribute = getattr(command_module, split_module[-1])
        # Test if the command is callable
        if not callable(command):
            logger.error("Command %s is not callable", command_attribute)
            return

        # Execute the command with arg parameters
        if type(args) in (list, tuple):
            command_attribute(*args)
        # Execute the command with kwargs parameters
        elif type(args) is dict:
            command_attribute(**args)
        else:
            logger.error("Invalid arugment for command %s", command)
            return

    @property
    def variables(self) -> dict:
        return self.buffer.variables

    @property
    def commands(self) -> dict:
        return self.buffer.commands
