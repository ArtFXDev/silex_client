from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
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
        "source_path": {
            "label": "Source path",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Select the file or the directory you want to copy",
        },
        "new_name": {
            "label": "New name",
            "type": str,
            "value": None,
            "tooltip": "Insert the new name for the given file",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        source_path: pathlib.Path = parameters["source_path"]
        new_name: str = parameters["new_name"]

        # Check the file(s) to copy
        if not os.path.exists(source_path):
            raise Exception(f"Source path {source_path} does not exists")

        new_name = os.path.splitext(new_name)[0]
        extension = os.path.splitext(source_path)[-1]
        new_name += extension
        new_path = os.path.join(os.path.dirname(source_path), new_name)
        logger.info("Renaming %s to %s", source_path, new_path)
        if os.path.exists(new_path):
            os.remove(new_path)
        os.rename(source_path, new_path)

        return {
            "source_path": source_path,
            "new_path": new_path,
        }
