from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    PathParameterMeta,
    RadioSelectParameterMeta,
    TextParameterMeta,
)

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import pathlib


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

    async def _prompt_override(
        self, file_path: pathlib.Path, action_query: ActionQuery
    ) -> str:
        """
        Helper to prompt the user for a new conform type and wait for its response
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
                "Override", "Keep existing", "Always override", "Always keep existing"
            ),
            name="existing_file",
            label="Existing file",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "existing_file": new_parameter,
            },
        )
        return response["existing_file"]

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
        logger.info("Renaming %s to %s", source_sequences, name_sequences)

        # Loop over all the files to rename
        for index, source_path in enumerate(source_paths):
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
                response = action_query.store.get("rename_override")
                if response is None:
                    response = await self._prompt_override(new_path, action_query)
                if response in ["Always override", "Always keep existing"]:
                    action_query.store["rename_override"] = response
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
