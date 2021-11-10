from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


from silex_client.utils.parameter_types import ListParameter
import shutil
import os
import pathlib

class Move(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "src": {
            "label": "File path",
            "type": ListParameter,
            "value": None,
        },
        "dst": {
            "label": "Destination directory",
            "type": pathlib.Path,
            "value": None,
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        src: pathlib.Path = parameters["src"]
        dst: pathlib.Path = str(parameters["dst"])

        # Check for file to copy
        if not os.path.exists(dst):
            raise Exception(f"{dst} doesn't exist.")

        for item in src:
            # Check for file to copy
            if not os.path.exists(item):
                raise Exception(f"{item} doesn't exist.")

            # remove if dst already exist
            # item : path of existing file/dir
            end_path = os.path.join(dst, os.path.basename(item))
            if os.path.isdir(end_path):
                shutil.rmtree(end_path)

            if os.path.isfile(end_path):
                os.remove(end_path)

            logger.info(f"source : {item}")
            logger.info(f"destination : {dst}")

            shutil.move(item, dst)
