from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.enums import ConflictBehaviour
from silex_client.utils.prompt import prompt_override, UpdateProgress
from silex_client.utils.files import find_sequence_from_path
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    PathParameterMeta,
)
from silex_client.utils.thread import execute_in_thread

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Rename(CommandBase):
    """
    Rename the given files
    """

    parameters = {
        "src": {
            "label": "Source path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Select the file or the directory you want to rename",
        },
        "name": {
            "label": "New name",
            "type": ListParameterMeta(str),
            "value": None,
            "tooltip": "Insert the new name for the given file",
        },
        "force": {
            "label": "Force override existing files",
            "type": bool,
            "value": True,
            "tooltip": "If a file already exists, it will be overriden without prompt",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        src_paths: List[pathlib.Path] = parameters["src"]
        new_names: List[str] = parameters["name"]
        force: bool = parameters["force"]

        src_sequences = fileseq.findSequencesInList(src_paths)
        name_sequences = fileseq.findSequencesInList(new_names)
        logger.info("Renaming %s to %s", src_sequences, name_sequences)

        new_paths = []
        label = self.command_buffer.label
        progress = SharedVariable(0)

        # Loop over all the files to rename
        async with UpdateProgress(
            self.command_buffer,
            action_query,
            progress,
            SharedVariable(len(src_paths)),
            0.2,
        ):
            for index, src_path in enumerate(src_paths):
                progress.value = index + 1
                self.command_buffer.label = f"{label} ({index+1}/{len(src_paths)})"

                new_name = new_names[index % len(new_names)]

                if not src_path.exists():
                    raise Exception(f"Source path {src_path} does not exists")

                # Find the sequence this file belongs to
                src_sequence = find_sequence_from_path(src_path)

                # Construct the new name
                extension = str(src_sequence.extension())
                new_name = os.path.splitext(new_name)[0] + extension
                new_path = src_path.parent / new_name

                # Handle override of existing file
                if new_path.exists() and force:
                    await execute_in_thread(os.remove, new_path)
                elif new_path.exists():

                    conflict_behaviour = action_query.store.get(
                        "file_conflict_behaviour"
                    )
                    if conflict_behaviour is None:
                        response = await prompt_override(self, new_path, action_query)
                    if response in [
                        ConflictBehaviour.ALWAYS_OVERRIDE,
                        ConflictBehaviour.ALWAYS_KEEP_EXISTING,
                    ]:
                        action_query.store["file_conflict_behaviour"] = response
                    if response in [
                        ConflictBehaviour.OVERRIDE,
                        ConflictBehaviour.ALWAYS_OVERRIDE,
                    ]:
                        force = True
                        await execute_in_thread(os.remove, new_path)
                    if response in [
                        ConflictBehaviour.KEEP_EXISTING,
                        ConflictBehaviour.ALWAYS_KEEP_EXISTING,
                    ]:
                        await execute_in_thread(os.remove, src_path)
                        continue

                await execute_in_thread(os.rename, src_path, new_path)
                new_paths.append(new_path)

        return {
            "source_paths": src_paths,
            "new_paths": new_paths,
        }
