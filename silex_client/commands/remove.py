from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import shutil
import os
import pathlib


class Remove(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        file_path: pathlib.Path = parameters.get("file_path")

        # Check for file to copy
        if not os.path.exists(file_path):
            raise Exception(
                "{} temporary file doesn't exist".format(file_path))

        # check already existing file
        if not os.path.exists(file_path):
            return

        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            os.removedirs(file_path)
        logger.info(f"OK remove {file_path}")
