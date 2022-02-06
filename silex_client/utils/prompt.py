"""
@author: TD gang
@github: https://github.com/ArtFXDev

Helper functions used for communication with the user
"""
import asyncio
import pathlib
from typing import Dict, Optional, Union

from silex_client.action.action_query import ActionQuery
from silex_client.action.command_sockets import CommandSockets
from silex_client.action.socket_buffer import SocketBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.enums import ConflictBehaviour
from silex_client.utils.socket_types import (
    TextType,
    RadioSelectType,
)

async def prompt(
    command_buffer: CommandBuffer,
    action_query: ActionQuery,
    inputs: Dict[str, Union[SocketBuffer, dict]],
) -> CommandSockets:
    """
    Add the given parameters to to current command parameters and ask an update from the user
    """
    command_parameters = command_buffer.get_inputs_helper(action_query)
    if not action_query.ws_connection.is_running:
        return command_parameters

    # Hide the existing parameters
    for input_buffer in command_buffer.inputs.values():
        input_buffer.hide = True

    # Cast the parameters that are dict into SocketBuffer
    socket_buffers: Dict[str, SocketBuffer] = {}
    for socket_name, socket in inputs.items():
        if isinstance(socket, SocketBuffer):
            socket_buffers[socket_name] = socket
            continue
        socket["parent"] = command_buffer
        socket_buffers[socket_name] = SocketBuffer.construct(socket, command_buffer)

    # Add the parameters to the command buffer's parameters
    command_buffer.inputs.update(socket_buffers)
    command_buffer.prompt = True

    await action_query.prompt_commands(end=action_query.current_command_index + 1)
    return command_parameters


async def prompt_override(
    command_buffer: CommandBuffer, file_path: pathlib.Path, action_query: ActionQuery
) -> ConflictBehaviour:
    """
    Helper to prompt the user for cases when we must override a file and wait for its response
    """
    # Create a new parameter to prompt for the new file path
    info_input = SocketBuffer(
        type=TextType("info"),
        name="info",
        label="Info",
        value=f"The path:\n{file_path}\nAlready exists",
    )
    behaviour_input = SocketBuffer(
        type=RadioSelectType(
            **{
                "Override": 0,
                "Keep existing": 2,
                "Always override": 1,
                "Always keep existing": 3,
            }
        ),
        name="conflict_behaviour",
        label="Conflict behaviour",
    )
    # Prompt the user to get the new path
    response = await prompt(
        command_buffer,
        action_query,
        {
            "info": info_input,
            "conflict_behaviour": behaviour_input,
        },
    )
    return ConflictBehaviour(int(response["conflict_behaviour"]))


class UpdateProgress:
    """
    Helper to update the progress field of the command asyncronously
    """
    def __init__(
        self,
        command_buffer: CommandBuffer,
        action_query: ActionQuery,
        progress: SharedVariable,
        update_time: float  = 0.2,
    ):
        self.command_buffer = command_buffer
        self.action_query = action_query
        self.progress = progress
        self.update_time = update_time
        self._task: Optional[asyncio.Task] = None

    async def update_progress(self):
        """
        Coroutine meant to be executed in a different task
        for non blocking update
        """
        while True:
            try:
                await asyncio.sleep(self.update_time)
                self.command_buffer.progress = int(self.progress.value * 100)
                await self.action_query.async_update_websocket()
            except asyncio.CancelledError:
                self.command_buffer.progress = 100
                await self.action_query.async_update_websocket()
                break

    async def __aenter__(self):
        self._task = asyncio.create_task(self.update_progress())
        return self._task

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if self._task is not None:
            self._task.cancel()
