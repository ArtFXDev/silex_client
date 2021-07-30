from __future__ import annotations
import uuid
import copy
import typing
from collections import OrderedDict
from collections.abc import Iterator
from dataclasses import dataclass, field

from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.merge import merge_data
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection


@dataclass()
class ActionBuffer(Iterator):
    """
    Store the state of an action, it is used as a comunication payload with the UI
    """

    # Define the mandatory keys and types for each attribibutes of a buffer
    STEP_TEMPLATE = {"index": int, "commands": list}
    COMMAND_TEMPLATE = {"path": str}

    name: str = field()
    return_code: int = field(default=0)
    uid: uuid.UUID = field(default=uuid.uuid1())

    def __init__(self, name: str, ws_connection: WebsocketConnection):
        self.name = name
        self.ws_connection = ws_connection
        self._commands = OrderedDict()

    def __iter__(self):
        if not self._commands:
            return iter([])

        # Initialize the step iterator
        self._step_iter = iter(self.commands.items())
        self._current_step = next(self._step_iter)

        # Initialize the command iterator
        self._command_iter = iter(self._current_step[1]["commands"])
        return self

    def __next__(self) -> dict:
        # Get the next command in the current step if available
        try:
            command = next(self._command_iter)
            return command
        # Get the next step available and rerun the loop
        except StopIteration:
            # No need to catch the StopIteration exception
            # Since it will just end the loop has we would want
            self._current_step = next(self._step_iter)
            self._command_iter = iter(self._current_step[1]["commands"])
            # TODO: Return a silex_client.commands.iter_step command instead
            return self.__next__()

    def _serialize(self):
        """
        Convert the action's data into json so it can be sent to the UI
        """
        pass

    def _deserialize(self, serealised_data):
        """
        Convert back the action's data from json into this object
        """
        pass

    def send(self):
        """
        Serialize and send this buffer to the UI though websockets
        """
        pass

    def receive(self, timeout: int):
        """
        Wait for the UI to send back a buffer and deserialize it
        """
        pass

    @property
    def variables(self) -> dict:
        variables = {}
        # Each command save its variable and they override the variables of the previous ones
        for command in self:
            variables.update(command.variables)
        return variables

    @property
    def commands(self) -> dict:
        return self._commands

    @commands.setter
    def commands(self, commands: dict):
        if not isinstance(commands, dict):
            logger.error("Invalid commands for action %s", self.name)

        filtered_commands = copy.deepcopy(commands)

        # Check if the steps are valid
        for name, step in commands.items():
            for key, value in self.STEP_TEMPLATE.items():
                if not isinstance(step, dict):
                    del filtered_commands[name]
                    break
                if key not in step or not isinstance(step[key], value):
                    del filtered_commands[name]
                    break

            # If the step has been deleted don't check the commands
            if name not in filtered_commands:
                continue

            # Check if the commands are valid
            for command in step["commands"]:
                for key, value in self.COMMAND_TEMPLATE.items():
                    if not isinstance(command, dict):
                        filtered_commands[name]["commands"].remove(command)
                        break
                    if key not in command or not isinstance(
                            command[key], value):
                        filtered_commands[name]["commands"].remove(command)
                        break

        # Override the existing commands with the new ones
        commands = merge_data(filtered_commands, dict(self.commands))

        # Convert the command dicts to CommandBuffers
        for step_name, step_value in commands.items():
            for index, command in enumerate(step_value["commands"]):
                # Create the command buffer and check if it is valid
                command_buffer = CommandBuffer(**command)
                if not command_buffer.valid:
                    del commands[step_name]["commands"][index]
                    continue
                # Override the dict to a CommandBuffer object
                commands[step_name]["commands"][index] = command_buffer

        # Sort the steps using the index key
        sort_cmds = sorted(commands.items(), key=lambda item: item[1]["index"])
        self._commands = OrderedDict(sort_cmds)
