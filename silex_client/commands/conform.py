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

class Conform(CommandBase):
    """
    Save current scene with context as path
    """

    parameters: CommandParameters = {
        "filename": { "label": "filename", "type": str, "value": "" }
    }


    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        task_id = action_query.context_metadata.get("task_id", "none")
        working_file = await gazu.files.build_working_file_path(task_id)
        if task_id == "none":
            logger.error("Invalid task_id !")
            return

        soft = await gazu.files.get_software_by_name(action_query.context_metadata.get("dcc", ""))
        extension = soft.get("file_extension", ".no")
        working_file += extension
        if extension == ".no":
            logger.error("Sofware not set in Kitsu, file extension will be invalid")
            return

        # if input file exist
        input_file = parameters.get("filename", "")
        if not os.path.exists(input_file):
            logger.error("Input file doesn't exist")
            return

        # if output file exist
        if os.path.exists(working_file):
            logger.error("Output file already exist")
            return

        # create folders structure
        working_folders = os.path.dirname(working_file)
        os.makedirs(working_folders)
        
        shutil.copy(input_file, working_file)
        print(working_file)
