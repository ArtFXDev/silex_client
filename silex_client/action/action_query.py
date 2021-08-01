from __future__ import annotations
import importlib
from typing import Union
from dataclasses import dataclass, field

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.log import logger
from silex_client.network.websocket import WebsocketConnection
from silex_client.utils.config import Config


@dataclass
class ActionQuery():
    """
    Initialize and execute a given action
    """

    #: The name of the action, it must be the same as the config file name
    action_name: str = field()
    ws_connection: WebsocketConnection = field(compare=False, repr=False)
    #: Config object that will resove the config
    config: Config = field(compare=False, repr=False)
    #: Dict of variable that store the metadata of the context
    environment: dict = field(default_factory=dict)

    def __post_init__(self):
        self.buffer = ActionBuffer(self.action_name, self.ws_connection)
        self._initialize_buffer()

    def execute(self) -> ActionBuffer:
        """
        Execute the action's commands in order,
        send and receive the buffer to the UI when nessesary
        """
        for command in self.buffer:
            command(self.buffer.variables)

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
        self.buffer.update_commands(action_commands)

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
        """
        Shortcut to get the variable of the buffer
        """
        return self.buffer.variables

    @property
    def commands(self) -> dict:
        """
        Shortcut to get the commands of the buffer
        """
        return self.buffer.commands
