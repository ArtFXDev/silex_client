from __future__ import annotations
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathList
from silex_client.utils.log import logger

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import pathlib


class Rename(CommandBase):
    """
    Rename the given files
    """

    parameters = {
        "source_paths": {
            "label": "Source path",
            "type": PathList,
            "value": None,
            "tooltip": "Select the file or the directory you want to rename",
        },
        "new_names": {
            "label": "New name",
            "type": list,
            "value": None,
            "tooltip": "Insert the new name for the given file",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        source_paths: List[pathlib.Path] = parameters["source_paths"]
        new_names: List[str] = parameters["new_names"]

        new_paths = []
        # Loop over all the files to copy
        for index, source_path in enumerate(source_paths):
            # If only one new name is given, this will still work thanks to the modulo
            new_name = new_names[index % len(new_names)]
            # Check the file to rename
            if not os.path.exists(source_path):
                raise Exception(f"Source path {source_path} does not exists")

            extension = source_path.suffix
            new_name = os.path.splitext(new_name)[0] + extension
            new_path = source_path.parent / new_name
            logger.info("Renaming %s to %s", source_path, new_path)
            if new_path.exists():
                os.remove(new_path)
            os.rename(source_path, new_path)
            new_paths.append(new_path)

        return {
            "source_paths": source_paths,
            "new_paths": new_paths,
        }
