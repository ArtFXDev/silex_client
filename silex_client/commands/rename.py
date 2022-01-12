from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta, PathParameterMeta

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

        new_paths = []

        source_sequences = fileseq.findSequencesInList(source_paths)
        name_sequences = fileseq.findSequencesInList(new_names)
        logger.info("Renaming %s to %s", source_sequences, name_sequences)

        # Loop over all the files to copy
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
                if source_path in [pathlib.Path(file_path) for file_path in sequence]
            )

            # Construct the new name
            extension = str(sequence.extension())
            new_name = os.path.splitext(new_name)[0] + extension
            new_path = source_path.parent / new_name
            if new_path.exists():
                os.remove(new_path)
            os.rename(source_path, new_path)
            new_paths.append(new_path)

        return {
            "source_paths": source_paths,
            "new_paths": new_paths,
        }
