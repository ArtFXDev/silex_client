from __future__ import annotations

import logging
import os
import pathlib
import re
import typing
from typing import Any, Dict
import gazu.files
import fileseq


import asyncio
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.commands.build_work_path import BuildWorkPath
from silex_client.utils import command_builder
from silex_client.core.context import Context
from silex_client.utils.files import expand_path
from silex_client.utils.log import flog
from silex_client.utils.parameter_types import TaskFileParameterMeta, TextParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery



class SelectPull(BuildWorkPath):

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):

        task = await gazu.task.get_task(action_query.context_metadata["task_id"])
        async def work_and_full_path(version: int) -> tuple[str, str]:
            work_path: str = await gazu.files.build_working_file_path(
                task, software=None, revision=version, sep=os.path.sep
            )
            full_path = f"{work_path}{extension}"
            return work_path, full_path

        # Build the work path
        initial_version = 1
        version = initial_version
        work_path, full_path = await work_and_full_path(initial_version)

        existing_sequences = fileseq.findSequencesOnDisk(os.path.dirname(full_path))

        # Change to the good version ===================================================================================
        matching_sequence = None
        for sequence in existing_sequences:
            # Check if the filename is present in any of the file sequences
            if pathlib.Path(full_path) in [
                pathlib.Path(path) for path in sequence
            ]:
                # Set the version to the latest of that sequence
                last_version = sequence.frameSet()[-1] + 1

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

        publishes = [publish]
        if not publish.is_dir():
            publish = publish.parent
        else:
            publishes = list(publish.iterdir())

    # get the associated dcc to extension ==========================================================================