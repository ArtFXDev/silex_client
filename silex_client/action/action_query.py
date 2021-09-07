from __future__ import annotations
from typing import Any
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

        if resolved_action is None:
            return
        if self.action_name not in resolved_action:
            logger.error("Invalid resolved action %s", self.action_name)
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

    @property
    def parameters(self) -> dict:
        """
        Helper to get a list of all the parameters of the action, 
        usually used for printing infos about the action
        """
        parameters = {}
        for step_name, step in self.commands.items():
            for command_index, command in enumerate(step["commands"]):
                parameters[f"{step_name}:{command_index}"] = list(command.parameters.keys())

        return parameters

    def set_parameter(self, parameter_name: str, value: Any) -> None:
        """
        Shortcut to set variables on the buffer easly
        """
        step = None
        index = None

        parameter_split = parameter_name.split(":")
        name = parameter_split[-1]
        if len(parameter_split) == 3:
            step = parameter_split[0]
            try:
                index = int(parameter_split[1])
            except TypeError:
                logger.error("Could not set parameter %s: Invalid parameter" % parameter_name)
                return
        elif len(parameter_split) == 2:
            try:
                index = int(parameter_split[1])
            except TypeError:
                step = parameter_split[0]

        # Guess the info that were not provided by taking the first match
        valid = False
        for command_path, parameters in self.parameters.items():
            command_step = command_path.split(":")[0]
            command_index = int(command_path.split(":")[1])
            if step is None and index is None and name in parameters:
                step = command_step
                index = command_index
                valid = True
                break
            elif step is None and index == command_index and name in parameters:
                step = command_step
                valid = True
                break
            elif index is None and step == command_step and name in parameters:
                index = command_index
                valid = True
                break
            elif step is not None and index is not None:
                if step == command_step and index == command_index and name in parameters:
                    valid = True
                    break

        if step is None or index is None or not valid:
            logger.error("Could not set parameter %s: The parameter does not exists" % parameter_name)
            return

        self.buffer.set_parameter(step, index, name, value)
