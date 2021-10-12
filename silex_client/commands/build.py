from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import gazu.files
import gazu.task

class Build(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
    }


    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        print(action_query.context_metadata)
        task = await gazu.task.get_task("ac0e79cf-e5ce-49ff-932f-6aed3d425e4a")
        working_files = await gazu.files.build_working_file_path(task["id"])
        print("WF")
        soft = await gazu.files.get_software_by_name("maya")
        working_files += soft.get("file_extension", ".nomedia")
        print(working_files)
