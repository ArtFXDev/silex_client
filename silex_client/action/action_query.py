"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

import asyncio
import copy
from concurrent import futures
from typing import Any, Iterator, Dict, Union, List, TYPE_CHECKING, Optional

import jsondiff

from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.action.action_buffer import ActionBuffer
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.utils.enums import Status, Execution
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.action.step_buffer import StepBuffer
    from silex_client.core.event_loop import EventLoop
    from silex_client.network.websocket import WebsocketConnection

class ActionQuery:
    """
    Initialize and execute a given action
    """

    def __init__(self, name: str, search_path: Optional[List[str]] = None):
        context = Context.get()
        metadata_snapshot = ReadOnlyDict(copy.deepcopy(context.metadata))
        resolved_config = Config(search_path).resolve_action(name)

        if resolved_config is None:
            return

        self.event_loop: EventLoop = context.event_loop
        self.ws_connection: WebsocketConnection = context.ws_connection

        self.buffer: ActionBuffer = ActionBuffer(name, context_metadata=metadata_snapshot)
        self._initialize_buffer(resolved_config, {"context_metadata": metadata_snapshot})
        self._buffer_diff = copy.deepcopy(self.buffer)
        self._task: Optional[asyncio.Task] = None

        context.register_action(self)

    def execute(self) -> futures.Future:
        """
        Register a task that will execute the action's commands in order

        The result value can be awaited with result = future.result(timeout)
        and the task can be canceled with future.cancel()
        """
        # If the action has no commands, don't execute it
        if not self.commands:
            logger.warning("Could not execute %s: The action has no commands", self.name)
            future: futures.Future = futures.Future()
            future.set_result(None)
            return future

        # Initialize the communication with the websocket server
        self.initialize_websocket()

        async def execute_commands() -> None:
            # Execut all the commands one by one
            for index, command in enumerate(self.iter_commands()):
                # Only run the command if it is valid
                if self.buffer.status in [Status.INVALID, Status.ERROR]:
                    logger.error(
                        "Stopping action %s because the buffer is invalid or errored out",
                        self.name,
                    )
                    break

                # If the command requires an input from user, wait for the response
                if command.ask_user:
                    commands_left = self.commands[index:]
                    for command_left in commands_left:
                        if command_left.ask_user:
                            command_left.status = Status.WAITING_FOR_RESPONSE
                    if self.ws_connection.is_running:
                        logger.info("Waiting for UI response")
                        await asyncio.wait_for(
                            await self.async_update_websocket(apply_response=True), None
                        )
                    # Put the commands back to initialized
                    for command_left in self.commands[index:]:
                        command_left.status = Status.INITIALIZED

                # Create a dictionary that only contains the name and the value of the parameters
                # without infos like the type, label...
                parameters = {
                    key: value.get("value", None)
                    for key, value in command.parameters.items()
                }

                # Get the input result
                input_value = None
                if command.input_path:
                    input_command = self.get_command(command.input_path)
                    input_value = input_command.output_result if input_command is not None else None

                # Run the executor and copy the parameters
                # to prevent them from being modified during execution
                logger.debug(
                    "Executing command %s for action %s", command.name, self.name
                )
                if self.execution_type == Execution.FORWARD:
                    await command.executor(
                        input_value, copy.deepcopy(parameters), self
                    )
                elif self.execution_type == Execution.BACKWARD:
                    await command.executor.undo(
                        input_value, copy.deepcopy(parameters), self
                    )

            # Inform the UI of the state of the action (either completed or sucess)
            await self.async_update_websocket()
            if self.ws_connection.is_running and not self.buffer.hide:
                await self.ws_connection.async_send("/dcc/action", "clearAction", {"uuid": self.buffer.uuid})

        async def create_task():
            self._task = self.event_loop.loop.create_task(execute_commands())
            await self._task

        # Execute the commands in the event loop
        return self.event_loop.register_task(create_task())

    def cancel(self):
        """
        Cancel the execution of the action
        """
        if self._task is None or self._task.done():
            return

        self._task.cancel()
        self.ws_connection.send("/dcc/action", "clearAction", {"uuid": self.buffer.uuid})

    def undo(self):
        self.execution_type = Execution.BACKWARD

    def redo(self):
        self.execution_type = Execution.FORWARD

    def _initialize_buffer(self, resolved_config: dict, custom_data: Union[dict, None] = None) -> None:
        """
        Initialize the buffer from the config
        """
        # If no config could be found or is invalid, the result is {}
        if not resolved_config:
            return

        # Make sure the required action is in the config
        if self.name not in resolved_config.keys():
            logger.error(
                "Could not resolve the action %s: The root key should be the same as the config file name",
            )
            return

        # Get the config related to the current task
        action_definition = resolved_config[self.name]
        action_definition["name"] = self.name
        if self.context_metadata.get("task_type") in action_definition.get("tasks", {}).keys():
            task_definition = action_definition["tasks"][self.context_metadata["task_type"]]
            action_definition = jsondiff.patch(action_definition, task_definition)

        # Apply any potential custom data
        if custom_data is not None:
            action_definition.update(custom_data)

        # Update the buffer with the new data
        self.buffer.deserialize(action_definition)

    def initialize_websocket(self) -> None:
        """
        Send a serialised version of the buffer to the websocket server, and store a copy of it
        """
        if not self.ws_connection.is_running or self.buffer.hide:
            return
        self._buffer_diff = copy.deepcopy(self.buffer)
        self.ws_connection.send("/dcc/action", "query", self._buffer_diff)

    def update_websocket(self, apply_response=False) -> futures.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        return self.event_loop.register_task(
            self.async_update_websocket(apply_response)
        )

    async def async_update_websocket(self, apply_response=False) -> asyncio.Future:
        """
        Send a diff between the current state of the buffer and the last saved state of the buffer
        """
        if not self.ws_connection.is_running or self.buffer.hide:
            future = self.event_loop.loop.create_future()
            future.set_result(None)
            return future

        diff = jsondiff.diff(self._buffer_diff.serialize(), self.buffer.serialize())
        self._buffer_diff = copy.deepcopy(self.buffer)

        confirm = await self.ws_connection.async_send("/dcc/action", "update", diff)

        def apply_update(response: asyncio.Future) -> None:
            if response.cancelled():
                return

            logger.debug("Applying update: %s", response.result())
            patch = jsondiff.patch(self.buffer.serialize(), response.result())
            self.buffer.deserialize(patch)
            self._buffer_diff = copy.deepcopy(self.buffer)

        if apply_response:
            return await self.ws_connection.action_namespace.register_update_callback(
                apply_update
            )
        else:
            return confirm

    @property
    def execution_type(self) -> Execution:
        """Shortcut to get the status of the action stored in the buffer"""
        return self.buffer.execution_type

    @execution_type.setter
    def execution_type(self, value: Execution) -> None:
        """Shortcut to get the status of the action stored in the buffer"""
        self.update_event.set()
        self.buffer.execution_type = value

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
    def commands(self) -> list[CommandBuffer]:
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
            command = parameter_split[0]
        elif len(parameter_split) != 1:
            logger.warning("Invalid parameter path: The given parameter path %s has too many separators")

        # Guess the info that were not provided by taking the first match
        index = None
        for parameter_path, parameters in self.parameters.items():
            parameter_step = parameter_path.split(":")[0]
            parameter_command = parameter_path.split(":")[1]
            # If only the parameter is provided
            if step is None and command is None and name in parameters:
                step = parameter_step
                index = parameter_command
                break
            # If the command name and the parameter are provided
            elif step is None and command == parameter_command and name in parameters:
                step = parameter_step
                index = parameter_command
                break
            # If everything is provided
            elif step is not None and command is not None:
                if (
                    step == parameter_step
                    and command == parameter_command
                    and name in parameters
                ):
                    index = parameter_command
                    break

        if step is None or index is None:
            logger.error(
                "Could not set parameter %s: The parameter does not exists",
                parameter_name,
            )
            return

        self.buffer.set_parameter(step, index, name, value)

    def get_command(self, command_path: str) -> Optional[CommandBuffer]:
        """
        Shortcut to get a command easly

        The command path is parsed, according to the scheme : <step>:<command>
        If you only provide a <command> the first occurence will be returned
        """

        command_split = command_path.split(":")
        name = command_split[-1]
        step = None

        if len(command_split) == 2:
            step = command_split[0]
        elif len(command_split) != 1:
            logger.warning("Invalid command path: The given command path %s has too many separators")
            return None

        # If the command path is explicit, get the command directly
        if step is not None:
            try:
                return self.buffer.steps[step].commands[name]
            except KeyError:
                logger.error("Could not retrieve the command %s: The command does not exists", command_path)
                return None

        # If only the command is given, get the first occurence
        for command in self.iter_commands():
            if command.name == name:
                return command

        logger.error("Could not retrieve the command %s: The command does not exists", command_path)
        return None
        

class CommandIterator(Iterator):
    """
    Iterator for the commands of an action_buffer
    """

    def __init__(self, action_buffer: ActionBuffer):
        self.action_buffer = action_buffer
        self.execution_type = copy.deepcopy(action_buffer.execution_type)
        self.command_index = -1

    def __iter__(self) -> CommandIterator:
        self.command_index = -1
        return self

    def __next__(self) -> CommandBuffer:
        commands = self.action_buffer.commands
        execution_type_transition = self.execution_type != self.action_buffer.execution_type
        self.execution_type = copy.deepcopy(self.action_buffer.execution_type)

        if self.action_buffer.execution_type == Execution.FORWARD:
            if not execution_type_transition:
                self.command_index += 1
        if self.action_buffer.execution_type == Execution.BACKWARD:
            if not execution_type_transition:
                self.command_index -= 1

        if self.command_index < 0:
            raise StopIteration

        try:
            command = commands[self.command_index]
            return command
        except IndexError:
            raise StopIteration
