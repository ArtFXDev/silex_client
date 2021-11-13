from __future__ import annotations
import contextlib
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

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
        "source_path": {
            "label": "Source path",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Select the file or the directory you want to copy",
        },
        "destination_dir": {
            "label": "Destination directory",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Select the directory in wich you want to copy you file(s)",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        source_path: pathlib.Path = parameters["source_path"]
        destination_dir: pathlib.Path = parameters["destination_dir"]

        # Check the file(s) to copy
        if not os.path.exists(parameters["source_path"]):
            raise Exception(f"Source path {source_path} does not exists")

        # Copy only if the files does not already existrs
        os.makedirs(str(destination_dir), exist_ok=True)
        logger.info("Copying %s to %s", source_path, destination_dir)
        with contextlib.suppress(shutil.SameFileError):
            shutil.copy(source_path, destination_dir)
        destination_path = os.path.join(destination_dir, os.path.basename(source_path))

        return {
            "source_path": source_path,
            "destination_dir": destination_dir,
            "destination_path": destination_path,
        }