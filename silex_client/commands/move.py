from __future__ import annotations
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.thread import execute_in_thread
import logging

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


from silex_client.utils.parameter_types import ListParameterMeta
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
            "type": ListParameterMeta(pathlib.Path),
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
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

        src: List[str] = [str(source) for source in parameters["src"]]
        dst: str = str(parameters["dst"])

        # Check for file to copy
        if not os.path.exists(dst):
            raise Exception(f"{dst} doesn't exist.")

        for item in src:
            # Check for file to copy
            if not os.path.exists(item):
                raise Exception(f"{item} doesn't exist.")

            # Execute the move in a different thread to not block the event loop
            def move():
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

            await execute_in_thread(move)

