from __future__ import annotations

import os
import typing
from typing import Any, Dict
import pathlib
import fileseq

import gazu.shot
import gazu.asset
import gazu.files
import gazu.task

from silex_client.action.command_base import CommandBase
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildWorkPath(CommandBase):
    """
    Build the path where the work files should be saved to
    """

    parameters = {
        "increment": {
            "type": bool,
            "value": False,
            "tooltip": "Increment the scene name",
        }
    }
    required_metadata = ["task_id", "dcc", "project_file_tree"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
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
            task, software=software, revision=version, sep=os.path.sep
        )
        full_path = f"{work_path}.{extension}"

        # Make sure to get the last version everytime
        if os.path.exists(full_path):
            # Find the last version on disk
            sequences = fileseq.findSequencesOnDisk(os.path.dirname(full_path))
            for sequence in sequences:
                if pathlib.Path(full_path) in [pathlib.Path(path) for path in sequence]:
                    version = sequence.frameSet()[-1]
            # Check if we need to increment
            if parameters["increment"]:
                version += 1

            # Build the file path again
            work_path = await gazu.files.build_working_file_path(
                task, software=software, revision=version, sep=os.path.sep
            )
            full_path = f"{work_path}.{extension}"
            
        return full_path
