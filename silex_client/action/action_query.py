from __future__ import annotations
from typing import Any
import typing
from typing import Union
import jsondiff
import copy
from concurrent import futures
import asyncio

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.log import logger
from silex_client.utils.enums import Status

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection
    from silex_client.core.event_loop import EventLoop
    from silex_client.resolve.config import Config


class ActionQuery():
    """
    Initialize and execute a given action
    """
    def __init__(self, name: str, config: Config, event_loop: EventLoop, ws_connection: WebsocketConnection, context_metadata: dict):
        self.config = config
        self.event_loop = event_loop
        self.ws_connection = ws_connection
        self.buffer = ActionBuffer(name, context_metadata=context_metadata)
        self._initialize_buffer({"context_metadata": context_metadata})
        self._buffer_diff = copy.deepcopy(self.buffer)

    def execute(self) -> Union[futures.Future, asyncio.Future]:
        """
        Register a task that will execute the action's commands in order

        The result value can be awaited with result = future.result(timeout)
        and the task can be canceled with future.cancel()
        """
        # Initialize the communication with the websocket server
        if not self.ws_connection.is_running:
            # If the websocket server is not running, don't send anything
            logger.debug("Could not execute the action %s: The websocket connection is not running", self.name)
            future = futures.Future()
            future.set_result(None)
            return future
        self.initialize_websocket()

        async def execute_in_loop():
            # Execut all the commands one by one
            for command in self.commands:
                # Only run the command if it is valid
                if self.buffer.status in [Status.INVALID, Status.ERROR]:
                    logger.error("Stopping action %s because the buffer is invalid", self.name)
                    return self.buffer
                # Create a dictionary that only contains the name and the value of the parameters
                # without infos like the type, label...
                parameters = {
                    key: value.get("value", None)
                    for key, value in command.parameters.items()
                }
                # Run the executor and copy the parameters
                # to prevent them from being modified during execution
                await command.executor(copy.deepcopy(parameters), self)

        return self.event_loop.register_task(execute_in_loop())

    def _initialize_buffer(self, custom_data: dict=None) -> None:
        """
        Initialize the buffer from the config
        """
        # Resolve the action config and conform it so it can be converted to objects
        resolved_action = self.config.resolve_action(self.name)
        self._conform_resolved_action(resolved_action)

        # Make sure the required action is in the config
        if self.name not in resolved_action.keys():
            logger.error("Could not initialise the action: The resolved config is invalid")
            return
        resolved_action = resolved_action[self.name]

        # Apply any potential custom data
        if custom_data is not None:
            resolved_action.update(custom_data)

        # Update the buffer with the new data
        self.buffer.deserialize(resolved_action)

    def _conform_resolved_action(self, data: Any):
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            if isinstance(value, dict) and key not in ["steps", "commands"]:
                value["name"] = key
            self._conform_resolved_action(value)

    def initialize_websocket(self) -> None:
        """
        Send a serialised version of the buffer to the websocket server, and store a copy of it
        """
        self._buffer_diff = copy.deepcopy(self.buffer)
        self.ws_connection.send("/action", "query", self._buffer_diff)

    def send_websocket(self) -> futures.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        diff = jsondiff.diff(self._buffer_diff.serialize(), self.buffer.serialize())
        return self.ws_connection.send("/action", "update", diff)

    async def async_send_websocket(self) -> asyncio.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        diff = jsondiff.diff(self._buffer_diff.serialize(), self.buffer.serialize())
        return await self.ws_connection.async_send("/action", "update", diff)

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
    def steps(self) -> list:
        """
        Shortcut to get the steps of the buffer
        """
        return list(self.buffer.steps.values())

    @property
    def commands(self) -> list:
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

        The format of the output is {<step>:<command> : parameters}
        """
        parameters = {}
        for step in self.steps:
            for command in step.commands.values():
                parameters[f"{step.name}:{command.name}"] = command.parameters

        return parameters

    def set_parameter(self, parameter_name: str, value: Any) -> None:
        """
        Shortcut to set variables on the buffer easly

        The parameter name is parsed, according to the scheme : <step>:<command>:<parameter>
        The missing values can be guessed if there is no ambiguity, only <parameter> is required
        """
        step = None
        command = None

        # Get the infos that are provided
        parameter_split = parameter_name.split(":")
        name = parameter_split[-1]
        if len(parameter_split) == 3:
            step = parameter_split[0]
            command = parameter_split[1]
        elif len(parameter_split) == 2:
            command = parameter_split[1]

        # Guess the info that were not provided by taking the first match
        valid = False
        for parameter_path, parameters in self.parameters.items():
            parameter_step = parameter_path.split(":")[0]
            parameter_command = parameter_path.split(":")[1]
            # If only the parameter is provided
            if step is None and command is None and name in parameters:
                step = parameter_step
                index = parameter_command
                valid = True
                break
            # If the command name and the parameter are provided
            elif step is None and command == parameter_command and name in parameters:
                step = parameter_step
                valid = True
                break
            # If everything is provided
            elif step is not None and command is not None:
                if step == parameter_step and command == parameter_command and name in parameters:
                    valid = True
                    break

        if step is None or index is None or not valid:
            logger.error(
                "Could not set parameter %s: The parameter does not exists",
                parameter_name)
            return

        self.buffer.set_parameter(step, index, name, value)
