from __future__ import annotations
from typing import Any

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.log import logger
from silex_client.utils.enums import Status
from silex_client.utils.config import Config
from silex_client.network.websocket import WebsocketConnection


class ActionQuery():
    """
    Initialize and execute a given action
    """
    def __init__(self, name: str, config: Config, context_metadata: dict):
        self.config = config
        self.buffer = ActionBuffer(name, context_metadata)
        self._initialize_buffer()

    def execute(self) -> ActionBuffer:
        """
        Execute the action's commands in order,
        send and receive the buffer to the UI when nessesary
        """
        for command in self.buffer:
            # Only run the command if it is valid
            if self.buffer.status is Status.INVALID:
                logger.error("Stopping action %s because the buffer is invalid",
                             self.name)
                return self.buffer
            # Create a shortened version of the parameters and pass them to the executor
            parameters = {
                key: value.get("value", None)
                for key, value in command.parameters.items()
            }
            # Run the executor
            command.executor(parameters, self.variables, self.buffer)

        return self.buffer

    def _initialize_buffer(self) -> None:
        """
        Initialize the buffer from the config
        """
        resolved_action = self.config.resolve_action(self.name)

        if resolved_action is None:
            return
        if self.name not in resolved_action:
            logger.error("Invalid resolved action %s", self.name)
            return

        action_commands = resolved_action[self.name]
        self.buffer.update_commands(action_commands)

    @property
    def name(self) -> str:
        """
        Shortcut to get the name  of the action stored in the buffer
        """
        return self.buffer.name

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
    def context_metadata(self) -> dict:
        """
        Shortcut to get the context's metadata  of the buffer
        """
        return self.buffer.context_metadata

    @property
    def parameters(self) -> dict:
        """
        Helper to get a list of all the parameters of the action,
        usually used for printing infos about the action
        """
        parameters = {}
        for step_name, step in self.commands.items():
            for command_index, command in enumerate(step["commands"]):
                parameters[f"{step_name}:{command_index}"] = list(
                    command.parameters.keys())

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
                logger.error("Could not set parameter %s: Invalid parameter",
                             parameter_name)
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
            elif step is None and index == command_index and name in parameters:
                step = command_step
                valid = True
            elif index is None and step == command_step and name in parameters:
                index = command_index
                valid = True
            elif step is not None and index is not None:
                if step == command_step and index == command_index and name in parameters:
                    valid = True

        if step is None or index is None or not valid:
            logger.error(
                "Could not set parameter %s: The parameter does not exists",
                parameter_name)
            return

        self.buffer.set_parameter(step, index, name, value)
