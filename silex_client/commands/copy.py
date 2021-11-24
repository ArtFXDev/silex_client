from __future__ import annotations
import contextlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
import logging

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import shutil
import os
import pathlib


class Copy(CommandBase):
    """
    Copy files and override if asked
    """

    parameters = {
        "src": {
            "label": "Source path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Select the file or the directory you want to copy",
        },
        "dst": {
            "label": "Destination directory",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Select the directory in wich you want to copy you file(s)",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        source_paths: List[pathlib.Path] = parameters["src"]
        destination_dirs: List[pathlib.Path] = parameters["dst"]

        destination_paths = []
        # Loop over all the files to copy
        for index, source_path in enumerate(source_paths):
            # If only one directory is given, this will still work thanks to the modulo
            destination_dir = destination_dirs[index % len(destination_dirs)]
            # Check the file to copy
            if not source_path.exists():
                raise Exception(f"Source path {source_path} does not exists")

            # Copy only if the files does not already exists
            os.makedirs(str(destination_dir), exist_ok=True)
            logger.info("Copying %s to %s", source_path, destination_dir)
            with contextlib.suppress(shutil.SameFileError):
                shutil.copy(source_path, destination_dir)
            destination_paths.append(destination_dir / source_path.name)

        return {
            "source_paths": source_paths,
            "destination_dirs": destination_dirs,
            "destination_paths": destination_paths,
        }
