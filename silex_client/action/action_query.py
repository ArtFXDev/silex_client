"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

import asyncio
import copy
import os
from concurrent import futures
from typing import TYPE_CHECKING, Iterator, Optional, Union

import jsondiff

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.connection import Connection
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger
from silex_client.utils.serialiser import silex_diff

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.core.event_loop import EventLoop
    from silex_client.network.websocket import WebsocketConnection


class ActionQuery:
    """
    This is the entry point to create, execute, and manipulate actions
    To create and execute an action, you can instantiate this class with the name of the
    action you want to execute and call execute()

    WARNING: To execute an action the silex's event loop must be running. To start
    the silex's event loop, use Context.get().start_services()
    """

    def __init__(
        self,
        name: str,
        definition: Optional[dict] = None,
        category="action",
        simplify=False,
        register=True,
    ):
        context = Context.get()

        # To prevent concurency problems, the action is running with its own
        # copy of the context at the time of its creation
        metadata_snapshot = ReadOnlyDict(copy.deepcopy(context.metadata))

        # The user can pass an action definition directly. If he doesn't provide any,
        # the action definition is resolved by looking at the action definition configs
        if not definition:
            resolved_definition = Config.get().resolve_action(name, category)
            if resolved_definition is not None:
                definition = resolved_definition[name]

        self.event_loop: EventLoop = context.event_loop
        self.ws_connection: WebsocketConnection = context.ws_connection
        self.execution_type = Execution.FORWARD

        self.buffer: ActionBuffer = ActionBuffer(
            name, context_metadata=metadata_snapshot
        )

        self.command_iterator: CommandIterator = self.iter_commands()
        self._buffer_diff = copy.deepcopy(self.buffer.serialize())
        self._task: Optional[asyncio.Task] = None
        self.closed = futures.Future()

        definition = {} if definition is None else definition
        self._initialize_buffer(definition, {"context_metadata": metadata_snapshot})

        # TODO: This should be done in the construct static method of buffers
        if simplify or os.getenv("SILEX_SIMPLE_MODE"):
            self.buffer.simplify = True
            for commands in self.commands:
                commands.hide = True

        if register:
            context.register_action(self)

    def __bool__(self):
        return bool(self.commands)

    async def execute_commands(self, step_by_step: bool = False) -> None:
        """
        Execute the commands one by one in order
        Starting from the last one
        """
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
            if (
                command.require_prompt(self)
                and self.execution_type is Execution.FORWARD
            ):
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
        command_statuses = []
        # Set the commands to WAITING_FOR_RESPONSE
        for index, command_left in enumerate(commands_prompt):
            await command_left.setup(self)
            if not command_left.require_prompt(self):
                end = start + index if start is not None else index
                break
            command_left.ask_user = True
            command_statuses.append(command_left.status)
            command_left.status = Status.WAITING_FOR_RESPONSE
            command_left.hide = False

        # Send the update to the UI and wait for its response
        while (
            self.ws_connection.is_running
            and not self.buffer.hide
            and self.commands[start].require_prompt(self)
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
            command_left.status = command_statuses[index]

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
        """Sync version of async_cancel, this can be called from the main thread"""
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
        """Sync version of async_undo, this can be called from the main thread"""
        self.event_loop.register_task(self.async_undo(all_commands))

    def redo(self):
        """Restart the action in formard mode"""
        if self.execution_type is not Execution.FORWARD:
            self.command_iterator.command_index -= 1
        self.execution_type = Execution.FORWARD
        if not self.is_running:
            self.execute()

    def stop(self):
        """Pause the execution of the action"""
        self.execution_type = Execution.PAUSE

    def _initialize_buffer(
        self, action_definition: dict, custom_data: Union[dict, None] = None
    ) -> None:
        """
        Initialize the buffer from the config
        """
        # If no config could be found or is invalid, the result is {}
        if not action_definition:
            return

        # Get the config related to the current task
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
    def current_command_index(self):
        """Get the index stored in the command iterator"""
        return self.command_iterator.command_index

    @property
    def name(self) -> str:
        """Shortcut to get the name  of the action stored in the buffer"""
        return self.buffer.name

    @property
    def commands(self) -> list[CommandBuffer]:
        """Shortcut to get the commands of the buffer"""
        return self.buffer.commands

    @property
    def context_metadata(self) -> dict:
        """Shortcut to get the context's metadata  of the buffer"""
        return self.buffer.context_metadata

    def iter_commands(self) -> CommandIterator:
        """
        Iterate over all the commands in order
        """
        return CommandIterator(self)

    def get_command(self, command_path: str) -> Optional[CommandBuffer]:
        """
        Shortcut to get a command easly
        """
        return self.buffer.get_command(command_path.split(Connection.SPLIT))


class CommandIterator(Iterator):
    """
    Iterator for the commands of an action_buffer.
    It acts as a pointer to a command index and uses the attribute
    <execution_type> of the action query to determine the next command
    """

    def __init__(self, action_query: ActionQuery):
        self.action_query = action_query
        self.command_index = -1

    def __iter__(self) -> CommandIterator:
        return self

    def __next__(self) -> CommandBuffer:
        commands = self.action_query.commands
        # We store the index in a temporary variable to not edit the real index
        # in case we raise a StopIteration
        new_index = self.command_index

        if self.action_query.execution_type == Execution.PAUSE:
            raise StopIteration
        # Increment the index according to the callback
        if self.action_query.execution_type == Execution.FORWARD:
            new_index += 1
        if self.action_query.execution_type == Execution.BACKWARD:
            new_index -= 1

        # Test if the command is out of bound and raise StopIteration if so
        if new_index < 0:
            raise StopIteration

        try:
            command = commands[new_index]
            self.command_index = new_index
            return command
        except IndexError as exception:
            raise StopIteration from exception
