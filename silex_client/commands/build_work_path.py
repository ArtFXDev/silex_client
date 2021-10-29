from __future__ import annotations

import os
import typing
from typing import Any, Dict

import gazu.shot
import gazu.asset
import gazu.files
import gazu.task

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildWorkPath(CommandBase):
    """
    Build the path where the work files should be saved to
    """

    required_metadata = ["task_id", "dcc"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Get informations about the current task
        task = await gazu.task.get_task(action_query.context_metadata["task_id"])
        if task is None:
            logger.error(
                "Could not build the work path: The given task %s does not exists",
                action_query.context_metadata["task_id"],
            )
            raise Exception(
                "Could not build the work path: The given task {} does not exists".format(
                    action_query.context_metadata["task_id"]
                )
            )

        # Get informations about the current software
        software = await gazu.files.get_software_by_name(
            action_query.context_metadata["dcc"]
        )
        if software is None:
            logger.error(
                "Could not build the work path: The given software %s does not exists",
                action_query.context_metadata["dcc"],
            )
            raise Exception(
                "Could not build the work path: The given task {} does not exists".format(
                    action_query.context_metadata["task_id"]
                )
            )
        extension: str = software.get("file_extension", ".no")

        # Build the work path
        version = 1
        work_path = await gazu.files.build_working_file_path(
            task, software=software, revision=version
        )
        full_path = f"{work_path}.{extension}"
        while os.path.exists(full_path):
            version += 1
            work_path = await gazu.files.build_working_file_path(
                task, software=software, revision=version
            )
            full_path = f"{work_path}.{extension}"

        logger.warning(full_path)
        return full_path
