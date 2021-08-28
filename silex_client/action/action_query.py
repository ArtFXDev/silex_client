from __future__ import annotations
from dataclasses import dataclass, field

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.log import logger
from silex_client.utils.config import Config
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.network.websocket import WebsocketConnection


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
            command(self.buffer.variables, ReadOnlyDict(self.environment))

        return self.buffer

    def _initialize_buffer(self) -> None:
        """
        Initialize the buffer from the config
        """
        resolved_action = self.config.resolve_action(self.action_name)

        if self.action_name not in resolved_action:
            logger.error("Invalid resolved action")
            return

        action_commands = resolved_action[self.action_name]
        self.buffer.update_commands(action_commands)

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
