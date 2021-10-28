from __future__ import annotations

import typing
from typing import Any, Dict

import gazu.shot
import gazu.asset
import gazu.files
import gazu.task

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPath(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "publish_type": {
            "label": "Insert publish type",
            "type": str,
            "value": None,
            "tooltip": "Insert the short name of the output type",
        },
    }

    required_metadata = ["entity_type", "entity_id", "task_type_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # Get the entity dict
        if action_query.context_metadata["entity_type"] == "shot":
            entity = await gazu.shot.get_shot(
                action_query.context_metadata["entity_id"]
            )
        else:
            entity = await gazu.asset.get_asset(
                action_query.context_metadata["entity_id"]
            )

        # Get the output type and the task type
        output_type = await gazu.files.get_output_type_by_short_name(
            parameters["publish_type"]
        )
        if output_type is None:
            raise Exception(
                "Could not get the output type %s: The output type does not exists",
                parameters["publish_type"],
            )
        task_type = await gazu.task.get_task_type(
            action_query.context_metadata["task_type_id"]
        )

        # Build the output path
        return await gazu.files.build_entity_output_file_path(
            entity, output_type, task_type
        )
