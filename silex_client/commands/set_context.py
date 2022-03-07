from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict

import gazu
from silex_client.action.command_base import CommandBase
from silex_client.core.context import Context
from silex_client.utils.parameter_types import TaskParameterMeta
from silex_client.utils.thread import execute_in_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetContext(CommandBase):
    """
    Set the context of the current session
    """

    parameters = {
        "task": {
            "label": "Select conform location",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Select the task where you can to conform your file",
        },
        "open_last_work": {
            "label": "Open last work scene",
            "type": bool,
            "value": False,
            "tooltip": "This will open the last work scene in the selected task",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        task_id: str = parameters["task"]
        os.environ["SILEX_TASK_ID"] = task_id
        await execute_in_thread(Context.get().compute_metadata)

        work_file = None

        if parameters["open_last_work"]:
            work_folder = os.path.dirname(
                await gazu.files.build_working_file_path(task_id)
            )
            files = [os.path.join(work_folder, f) for f in os.listdir(work_folder)]
            work_files = list(filter(os.path.isfile, files))
            work_files.sort(key=lambda x: os.path.getmtime(x))

            if len(work_files) > 0:
                work_file = work_files[-1]

        return {
            "open_last_work": not (
                parameters["open_last_work"] and work_file is not None
            ),
            "work_file": work_file,
        }
