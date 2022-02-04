import asyncio
import pathlib
from typing import Optional

from silex_client.action.command_base import CommandBase
from silex_client.action.action_query import ActionQuery
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.enums import ConflictBehaviour
from silex_client.utils.parameter_types import (
    TextParameterMeta,
    RadioSelectParameterMeta,
)


async def prompt_override(
    command_base: CommandBase, file_path: pathlib.Path, action_query: ActionQuery
) -> ConflictBehaviour:
    """
    Helper to prompt the user for cases when we must override a file and wait for its response
    """
    # Create a new parameter to prompt for the new file path
    info_parameter = ParameterBuffer(
        type=TextParameterMeta("info"),
        name="info",
        label="Info",
        value=f"The path:\n{file_path}\nAlready exists",
    )
    new_parameter = ParameterBuffer(
        type=RadioSelectParameterMeta(
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
    response = await command_base.prompt_user(
        action_query,
        {
            "info": info_parameter,
            "conflict_behaviour": new_parameter,
        },
    )
    return ConflictBehaviour(response["conflict_behaviour"])


class UpdateProgress:
    def __init__(
        self,
        command_buffer: CommandBuffer,
        action_query: ActionQuery,
        progress: SharedVariable,
        progress_total: SharedVariable,
        update_time: float,
    ):
        self.command_buffer = command_buffer
        self.action_query = action_query
        self.progress = progress
        self.progress_total = progress_total
        self.update_time = update_time
        self._task: Optional[asyncio.Task] = None

    async def update_progress(self):
        while True:
            try:
                await asyncio.sleep(self.update_time)
                self.command_buffer.progress = int(
                    (self.progress.value / self.progress_total.value) * 100
                )
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
