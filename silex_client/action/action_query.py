"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

import asyncio
import copy
import os
from concurrent import futures
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

import jsondiff

from silex_client.action.action_buffer import ActionBuffer
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger
from silex_client.utils.serialiser import silex_diff

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

    def __init__(
        self,
        name: str,
        resolved_config: Optional[dict] = None,
        category="action",
        simplify=False,
    ):
        context = Context.get()
        metadata_snapshot = ReadOnlyDict(copy.deepcopy(context.metadata))
        if resolved_config is None:
            resolved_config = Config.get().resolve_action(name, category)

        if resolved_config is None:
            self.buffer = ActionBuffer("none")
            return

        self.event_loop: EventLoop = context.event_loop
        self.ws_connection: WebsocketConnection = context.ws_connection

        self.buffer: ActionBuffer = ActionBuffer(
            name, context_metadata=metadata_snapshot
        )
        self._initialize_buffer(
            resolved_config, {"context_metadata": metadata_snapshot}
        )

        if simplify or os.getenv("SILEX_SIMPLE_MODE"):
            self.buffer.simplify = True
            for commands in self.commands:
                commands.hide = True

        self.command_iterator: CommandIterator = self.iter_commands()
        self._buffer_diff = copy.deepcopy(self.buffer.serialize())
        self._task: Optional[asyncio.Task] = None
        self.closed = futures.Future()

        context.register_action(self)

    async def execute_commands(self, step_by_step: bool = False) -> None:
        command_iterator = self.command_iterator
        if step_by_step:
            command_iterator = [next(self.command_iterator)]

        # Execut all the commands one by one
        for command in command_iterator:
            # Set the status to initialized
            command.status = Status.INITIALIZED
            # Only run the command if it is valid
            if self.buffer.status in [Status.INVALID, Status.ERROR]:
                logger.error(
                    "Stopping action %s because the buffer is invalid or errored out",
                    self.name,
                )
                break

            # If the command requires an input from user, wait for the response
            if command.require_prompt() and self.execution_type is Execution.FORWARD:
                await self.prompt_commands()

            # Setup the command
            await command.setup(self)

            # Execution of the command
            await command.execute(self, self.execution_type)

        # Inform the UI of the state of the action (either completed or sucess)
        await self.async_update_websocket()

    def execute(self, batch=False, step_by_step: bool = False) -> futures.Future:
        """
        Register a task that will execute the action's commands in order

        The result value can be awaited with result = future.result(timeout)
        and the task can be canceled with future.cancel()
        """
        # If the action has no commands or is already running, don't execute it
        if not self.commands or self.is_running:
            if not self.commands:
                logger.warning(
                    "Could not execute %s: The action has no commands", self.name
                )
            if not self.is_running:
                logger.warning(
                    "Could not execute %s: The action is already running", self.name
                )
            future: futures.Future = futures.Future()
            future.set_result(None)
            return future

        # The batch mode just set the action to hidden
        if batch:
            self.buffer.hide = True

        # Initialize the communication with the websocket server
        self.initialize_websocket()

        async def create_task():
            # Execute the task that will run all the commands
            self._task = self.event_loop.loop.create_task(
                self.execute_commands(step_by_step)
            )
            await self._task

        # Execute the commands in the event loop
        return self.event_loop.register_task(create_task())

    async def prompt_commands(self, start: int = None, end: int = None):
        """
        Ask a user input for a given range of commands, only the commands that
        require an input will wait for a response
        """
        if start is None:
            start = self.current_command_index

        # Get the range of commands
        commands_prompt = self.commands[start:end]
        # Set the commands to WAITING_FOR_RESPONSE
        for index, command_left in enumerate(commands_prompt):
            if not command_left.require_prompt():
                end = start + index if start is not None else index
                break
            command_left.ask_user = True
            await command_left.setup(self)
            command_left.status = Status.WAITING_FOR_RESPONSE
            command_left.hide = False

        # Send the update to the UI and wait for its response
        while (
            self.ws_connection.is_running
            and not self.buffer.hide
            and self.commands[start].require_prompt()
        ):
            # Call the setup on all the commands
            for command in self.commands[start:end]:
                await command.setup(self)
            # Wait for a response from the UI
            logger.debug("Waiting for UI response")
            await asyncio.wait_for(
                await self.async_update_websocket(apply_response=True), None
            )

        # Put the commands back to initialized
        for index, command_left in enumerate(self.commands[start:end]):
            command_left.ask_user = False
            command_left.status = Status.INITIALIZED

        await asyncio.wait_for(await self.async_update_websocket(), None)

    async def async_cancel(self, emit_clear: bool = True):
        """
        Cancel the execution of the action
        """
        if self._task is None or self._task.done():
            return

        if emit_clear and self.ws_connection.is_running:
            self.ws_connection.send(
                "/dcc/action", "clearAction", {"uuid": self.buffer.uuid}
            )

        self._task.cancel()

    def cancel(self, emit_clear: bool = True):
        future = self.event_loop.register_task(self.async_cancel(emit_clear))
        future.result()

    async def async_undo(self, all_commands: bool = False):
        """
        Cancel the action if running and restart it backward
        """
        if self.is_running and self._task is not None:
            await self.async_cancel(emit_clear=False)
            if self.execution_type is not Execution.BACKWARD:
                self.command_iterator.command_index += 1

        for command in self.commands[self.current_command_index :]:
            command.status = Status.INITIALIZED

        self.execution_type = Execution.BACKWARD
        await self.execute_commands(step_by_step=not all_commands)

    def undo(self, all_commands: bool = False):
        self.event_loop.register_task(self.async_undo(all_commands))

    def redo(self):
        if self.execution_type is not Execution.FORWARD:
            self.command_iterator.command_index -= 1
        self.execution_type = Execution.FORWARD
        if not self.is_running:
            self.execute()

    def stop(self):
        self.execution_type = Execution.PAUSE

    def _initialize_buffer(
        self, resolved_config: dict, custom_data: Union[dict, None] = None
    ) -> None:
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
        if (
            self.context_metadata.get("task_type")
            in action_definition.get("tasks", {}).keys()
        ):
            task_definition = action_definition["tasks"][
                self.context_metadata["task_type"]
            ]
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
        self._buffer_diff = copy.deepcopy(self.buffer.serialize())
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
        serialized_buffer = self.buffer.serialize()
        diff = silex_diff(self._buffer_diff, serialized_buffer)

        if (
            not self.ws_connection.is_running
            or self.buffer.hide
            or not (diff or apply_response)
        ):
            future = self.event_loop.loop.create_future()
            future.set_result(None)
            return future

        serialized_buffer = self.buffer.serialize()
        diff = silex_diff(self._buffer_diff, serialized_buffer)
        self._buffer_diff = serialized_buffer
        diff["uuid"] = self.buffer.uuid

        confirm = await self.ws_connection.async_send("/dcc/action", "update", diff)

        def apply_update(response: asyncio.Future) -> None:
            if response.cancelled():
                return

            logger.debug("Applying update: %s", response.result())
            self.buffer.deserialize(response.result())
            self._buffer_diff = self.buffer.serialize()

        if apply_response:
            return await self.ws_connection.action_namespace.register_update_callback(
                self.buffer.uuid, apply_update
            )
        return confirm

    @property
    def current_command(self):
        """Get the current command or the last command before stopping"""
        return self.commands[self.current_command_index]

    @property
    def is_running(self):
        """Check if the action is currently running"""
        return not (self._task is None or self._task.done())

    @property
    def execution_type(self) -> Execution:
        """Shortcut to get the status of the action stored in the buffer"""
        return self.buffer.execution_type

    @property
    def current_command_index(self):
        """Get the index stored in the command iterator"""
        return self.command_iterator.command_index

    @execution_type.setter
    def execution_type(self, value: Execution) -> None:
        """Shortcut to get the status of the action stored in the buffer"""
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
    def store(self) -> Dict[str, Any]:
        """Shortcut to get the variable of the buffer"""
        return self.buffer.store

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

    def set_parameter(self, parameter_name: str, value: Any, **kwargs) -> None:
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
            logger.warning(
                "Invalid parameter path: The given parameter path %s has too many separators",
                parameter_name,
            )

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

        self.buffer.set_parameter(step, index, name, value, **kwargs)

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
            logger.warning(
                "Invalid command path: The given command path %s has too many separators",
                command_path,
            )
            return None

        # If the command path is explicit, get the command directly
        if step is not None:
            try:
                return self.buffer.steps[step].commands[name]
            except KeyError:
                logger.error(
                    "Could not retrieve the command %s: The command does not exists",
                    command_path,
                )
                return None

        # If only the command is given, get the first occurence
        for command in self.iter_commands():
            if command.name == name:
                return command

        logger.error(
            "Could not retrieve the command %s: The command does not exists",
            command_path,
        )
        return None


class CommandIterator(Iterator):
    """
    Iterator for the commands of an action_buffer
    """

    def __init__(self, action_buffer: ActionBuffer):
        self.action_buffer = action_buffer
        self.command_index = -1

    def __iter__(self) -> CommandIterator:
        return self

    def __next__(self) -> CommandBuffer:
        commands = self.action_buffer.commands
        # We store the index in a temporary variable to not edit the real index
        # in case we raise a StopIteration
        new_index = self.command_index

        if self.action_buffer.execution_type == Execution.PAUSE:
            raise StopIteration
        # Increment the index according to the callback
        if self.action_buffer.execution_type == Execution.FORWARD:
            new_index += 1
        if self.action_buffer.execution_type == Execution.BACKWARD:
            new_index -= 1

        # Test if the command is out of bound and raise StopIteration if so
        if new_index < 0:
            raise StopIteration

        try:
            command = commands[new_index]
            self.command_index = new_index
            return command
        except IndexError:
            raise StopIteration
