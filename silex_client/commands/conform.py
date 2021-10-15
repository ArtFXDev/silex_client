from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase, CommandParameters
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import gazu.files
import gazu.task
import shutil
import re
import pathlib
class file:
    pass
class Conform(CommandBase):
    """
    Save current scene with context as path
    """

    parameters: CommandParameters = {
        "filename": { "label": "filename", "type": file , "value": "" }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        task_id = action_query.context_metadata.get("task_id", "none")
        working_file = await gazu.files.build_working_file_path(task_id)
        if task_id == "none":
            logger.error("Invalid task_id !")
            raise Exception("Invalid task_id !")
        
        # if input file exist
        input_file = parameters.get("filename", "")
        if not os.path.exists(input_file):
            logger.error("Input file doesn't exist")
            raise Exception("Input file doesn't exist")

        extension = input_file.split(".")[-1]
        extension = extension if '.' in extension else f".{extension}" 
        working_file += extension


        # get filename without extension
        filename = os.path.basename(working_file)
        working_file_without_extension = os.path.splitext(filename)[0]
        working_folders = os.path.dirname(working_file)
        
        #get current version
        version = re.findall("[0-9]*$", working_file_without_extension)
        version = version[0] if len(version) > 0 else ""  # get last number of file name
        zf = len(version)
        version = int(version)
        if version == "" :
            logger.error("Failed to get version from regex")
            raise Exception("Failed to get version from regex")

        # if output file exist
        file_without_version = re.findall("(?![0-9]*$).", working_file_without_extension)
        file_without_version = ''.join(file_without_version)

        while os.path.exists(working_file):
            version += 1
            working_file = os.path.join(working_folders, f"{file_without_version}{str(version).zfill(zf)}{extension}")

        # create folders structure
        if not os.path.exists(working_folders):
            os.makedirs(working_folders)
        
        shutil.copy(input_file, working_file)
