from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict

import fileseq
import gazu
from silex_client.action.command_base import CommandBase
from silex_client.utils.log import flog

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
        },
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

        # Get information about the current software
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

        async def work_and_full_path(version: int) -> tuple[str, str]:
            work_path: str = await gazu.files.build_working_file_path(
                task, software=software, revision=version, sep=os.path.sep
            )
            full_path = f"{work_path}.{extension}"
            return work_path, full_path

        # Build the work path
        initial_version = 1
        version = initial_version
        work_path, full_path = await work_and_full_path(initial_version)

        existing_sequences = fileseq.findSequencesOnDisk(os.path.dirname(full_path))
        flog.info(existing_sequences)

        # Only get the sequences of that software
        software_sequences = [
            seq
            for seq in existing_sequences
            if software["file_extension"] in seq.extension()
        ]
        flog.info(software_sequences)

        matching_sequence = None

        for sequence in software_sequences:
            # Check if the filename is present in any of the file sequences
            if pathlib.Path(work_path).stem in [
                pathlib.Path(path).stem for path in sequence
            ]:
                # Set the version to the latest of that sequence
                last_version = sequence.frameSet()[-1]

                # If the version is greater, use that
                if last_version > version:
                    version = last_version
                    matching_sequence = sequence

        # We also increment when an existing sequence was found
        if parameters["increment"]:
            version += 1

        if version != initial_version:
            # Rebuild the file path again with the new version
            _, full_path = await work_and_full_path(version)

        flog.info(full_path)

        return full_path

