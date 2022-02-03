from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.prompt import prompt_override, UpdateProgress
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
        source_paths: List[pathlib.Path] = parameters["src"]
        new_names: List[str] = parameters["name"]
        force: bool = parameters["force"]

        new_paths = []

        source_sequences = fileseq.findSequencesInList(source_paths)
        name_sequences = fileseq.findSequencesInList(new_names)
        label = self.command_buffer.label
        logger.info("Renaming %s to %s", source_sequences, name_sequences)
        progress = SharedVariable(0)

        # Loop over all the files to rename
        async with UpdateProgress(
            self.command_buffer,
            action_query,
            progress,
            SharedVariable(len(source_paths)),
            0.2,
        ):
            for index, source_path in enumerate(source_paths):
                progress.value = index + 1
                self.command_buffer.label = f"{label} ({index+1}/{len(source_paths)})"
                # If only one new name is given, this will still work thanks to the modulo
                new_name = new_names[index % len(new_names)]
                # Check the file to rename
                if not os.path.exists(source_path):
                    raise Exception(f"Source path {source_path} does not exists")

                # Find the sequence this file belongs to
                sequence = next(
                    sequence
                    for sequence in source_sequences
                    if source_path
                    in [pathlib.Path(str(file_path)) for file_path in sequence]
                )

                # Construct the new name
                extension = str(sequence.extension())
                new_name = os.path.splitext(new_name)[0] + extension
                new_path = source_path.parent / new_name

                # Handle override of existing file
                if new_path.exists() and force:
                    await execute_in_thread(os.remove, new_path)
                elif new_path.exists():
                    response = action_query.store.get("file_conflict_policy")
                    if response is None:
                        response = await prompt_override(self, new_path, action_query)
                    if response in ["Always override", "Always keep existing"]:
                        action_query.store["file_conflict_policy"] = response
                    if response in ["Override", "Always override"]:
                        force = True
                        await execute_in_thread(os.remove, new_path)
                    if response in ["Keep existing", "Always keep existing"]:
                        await execute_in_thread(os.remove, source_path)
                        new_paths.append(new_path)
                        continue

                await execute_in_thread(os.rename, source_path, new_path)
                new_paths.append(new_path)

        return {
            "source_paths": source_paths,
            "new_paths": new_paths,
        }
