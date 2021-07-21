import importlib
from typing import Union

from silex_client.network.websocket import WebsocketConnection
from silex_client.action.config import ActionConfig
from silex_client.action.buffer import ActionBuffer
from silex_client.utils.log import logger


class ActionQuery():
    """
    Initialize and execute a given action
    """
    def __init__(self, action_name: str, ws_connection: WebsocketConnection):
        self.action_name = action_name
        self.config = ActionConfig()
        self.buffer = ActionBuffer(ws_connection)
        pass

    def execute(self) -> ActionBuffer:
        """
        Execute the action's commands in order,
        send and receive the buffer to the UI when nessesary
        """
        return self.buffer

    def _initialize_buffer(self) -> None:
        """
        Initialize the buffer from the config
        """
        pass

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
