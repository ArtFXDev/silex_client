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


class MoveFile(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": pathlib.Path,
            "value": None,
        },
        "dst_dir": {
            "label": "Destination directory",
            "type": pathlib.Path,
            "value": None,
        },
        "from_temp": {
            "label": "Copy from temp directory",
            "type": bool,
            "value": False,
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        file_path: pathlib.Path = parameters.get("file_path")
        dst_dir: pathlib.Path = parameters.get("dst_dir")
        file_name_with_extension: str = str(file_path).split(os.path.sep)[-1]
        dst_path: pathlib.Path = os.path.join(dst_dir, file_name_with_extension)

        # Check for file to copy
        if not os.path.exists(file_path):
            raise Exception(
                "{} temporary file doesn't exist".format(file_path))

        # check already existing file
        if os.path.exists(dst_path):
            os.remove(dst_path)
        
        logger.info(f"destination : {dst_path}")
        logger.info(f"source : {dst_dir}")
        logger.info(f"file : {file_path}")
        
        # move file to location
        os.makedirs(str(dst_dir), exist_ok=True)
        shutil.move(file_path, dst_path)

        
        # Delete temp dir
        if parameters.get('fromm_temp'):
            temp: pathlib.Path = pathlib.Path(file_path)
            temp_dir: pathlib.Path = temp.parents[0]
            os.rmdir(temp_dir)
