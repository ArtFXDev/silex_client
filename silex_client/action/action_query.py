"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

import asyncio
import copy
from concurrent import futures
from typing import Any, Iterator, Dict, Union, List, TYPE_CHECKING

import jsondiff

from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.enums import Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.action.step_buffer import StepBuffer
    from silex_client.core.event_loop import EventLoop
    from silex_client.network.websocket import WebsocketConnection
    from silex_client.resolve.config import Config


class ActionQuery:
    """
    Initialize and execute a given action
    """

    def __init__(
        self,
        name: str,
        config: Config,
        event_loop: EventLoop,
        ws_connection: WebsocketConnection,
        context_metadata: Dict[str, Any],
    ):
        self.config = config
        self.event_loop = event_loop
        self.ws_connection = ws_connection
        self.buffer = ActionBuffer(name, context_metadata=context_metadata)
        self._initialize_buffer({"context_metadata": context_metadata})
        self._buffer_diff = copy.deepcopy(self.buffer)

    def execute(self) -> futures.Future:
        """
        Register a task that will execute the action's commands in order

        The result value can be awaited with result = future.result(timeout)
        and the task can be canceled with future.cancel()
        """
        # Initialize the communication with the websocket server
        if self.ws_connection.is_running:
            self.initialize_websocket()

        async def execute_commands():
            # Pass the result of every command to pass it to the next one
            upstream_result = None
            # Execut all the commands one by one
            for command in self.iter_commands():
                # Only run the command if it is valid
                if self.buffer.status in [Status.INVALID, Status.ERROR]:
                    logger.error(
                        "Stopping action %s because the buffer is invalid", self.name
                    )
                    return self.buffer
                # Create a dictionary that only contains the name and the value of the parameters
                # without infos like the type, label...
                parameters = {
                    key: value.get("value", None)
                    for key, value in command.parameters.items()
                }
                # Run the executor and copy the parameters
                # to prevent them from being modified during execution
                logger.debug(
                    "Executing command %s for action %s", command.name, self.name
                )
                upstream_result = await command.executor(
                    upstream_result, copy.deepcopy(parameters), self
                )

        # Execute the commands in the event loop
        future = self.event_loop.register_task(execute_commands())

        def on_action_completed(task):
            # Inform the UI of the state of the action (either completed or sucess)
            if self.ws_connection.is_running:
                self.update_websocket()

        future.add_done_callback(on_action_completed)
        return future

    def _initialize_buffer(self, custom_data: Union[dict, None] = None) -> None:
        """
        Initialize the buffer from the config
        """
        # Resolve the action config and conform it so it can be converted to objects
        resolved_action = self.config.resolve_action(self.name)
        self._conform_resolved_action(resolved_action)

        # If no config could be found, the result is none
        if resolved_action is None:
            return

        # Make sure the required action is in the config
        if self.name not in resolved_action.keys():
            logger.error(
                "Could not initialise the action: The resolved config is invalid"
            )
            return
        resolved_action = resolved_action[self.name]

        # Apply any potential custom data
        if custom_data is not None:
            resolved_action.update(custom_data)

        # Update the buffer with the new data
        self.buffer.deserialize(resolved_action)

    def _conform_resolved_action(self, data: dict):
        """
        When an action comes from a yaml, the data is not organised the same
        (It follows a different schema to make the yaml less verbose)

        This conform the data for the command buffer dataclass
        """
        if not isinstance(data, dict):
            return

        # To convert the yaml into real objects, there is some missing attributes that
        for key, value in data.items():
            # TODO: Find a better way to do this,
            # we can't name a step "steps" or "parameters" with this method
            if isinstance(value, dict) and key not in [
                "steps",
                "commands",
                "parameters",
            ]:
                value["name"] = key
            self._conform_resolved_action(value)

    def initialize_websocket(self) -> None:
        """
        Send a serialised version of the buffer to the websocket server, and store a copy of it
        """
        self._buffer_diff = copy.deepcopy(self.buffer)
        self.ws_connection.send("/dcc/action", "query", self._buffer_diff)

    def update_websocket(self) -> futures.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        return self.event_loop.register_task(self.async_update_websocket())

    async def async_update_websocket(self) -> asyncio.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        diff = jsondiff.diff(self._buffer_diff.serialize(), self.buffer.serialize())

        await self.ws_connection.async_send("/dcc/action", "update", diff)

        def apply_update(response: asyncio.Future) -> None:
            if response.cancelled():
                return

            patch = jsondiff.patch(self.buffer.serialize(), response.result())
            self.buffer.deserialize(patch)
            self._buffer_diff = copy.deepcopy(self.buffer)

        return await self.ws_connection.action_namespace.register_update_callback(
            apply_update
        )

    @property
    def name(self) -> str:
        """Shortcut to get the name  of the action stored in the buffer"""
        return self.buffer.name

    @property
    def status(self) -> Status:
        """Shortcut to get the status of the action stored in the buffer"""
        return self.buffer.status

    @property
    def variables(self) -> Dict[str, Any]:
        """Shortcut to get the variable of the buffer"""
        return self.buffer.variables

    @property
    def steps(self) -> List[StepBuffer]:
        """Shortcut to get the steps of the buffer"""
        return list(self.buffer.steps.values())

    @property
    def commands(self) -> list:
        """Shortcut to get the commands of the buffer"""
        return self.buffer.commands

    @property
    def context_metadata(self) -> dict:
        """Shortcut to get the context's metadata  of the buffer"""
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

    def iter_commands(self) -> CommandIterator:
        """
        Iterate over all the commands in order
        """
        return CommandIterator(self.buffer)

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
                if (
                    step == parameter_step
                    and command == parameter_command
                    and name in parameters
                ):
                    valid = True
                    break

        if step is None or index is None or not valid:
            logger.error(
                "Could not set parameter %s: The parameter does not exists",
                parameter_name,
            )
            return

        self.buffer.set_parameter(step, index, name, value)


class CommandIterator(Iterator):
    """
    Iterator for the commands of an action_buffer
    """

    def __init__(self, action_buffer: ActionBuffer):
        self.action_buffer = action_buffer
        self.command_index = 0
        self.action_index = 0

    def __iter__(self) -> CommandIterator:
        self.action_index = 0
        return self

    def __next__(self) -> CommandBuffer:
        commands = self.action_buffer.commands
        if self.action_index < len(commands):
            command = commands[self.action_index]
            self.action_index += 1
            return command

        raise StopIteration
