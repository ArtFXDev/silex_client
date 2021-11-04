from __future__ import annotations

import os
import uuid
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
    Build the path where the output files should be saved to
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

        # Get the output type
        output_type = await gazu.files.get_output_type_by_short_name(
            parameters["publish_type"]
        )
        if output_type is None:
            logger.error(
                "Could not build the output type %s: The output type does not exists in the zou database",
                parameters["publish_type"],
            )
            raise Exception(
                "Could not build the output type %s: The output type does not exists in the zou database",
                parameters["publish_type"],
            )

        # Get the task type
        task_type = await gazu.task.get_task_type(
            action_query.context_metadata["task_type_id"]
        )
        if task_type is None:
            logger.error(
                "Could not get the task type %s: The task type does not exists",
                action_query.context_metadata["task_type_id"],
            )
            raise Exception(
                "Could not get the task type %s: The task type does not exists",
                action_query.context_metadata["task_type_id"],
            )

        # Build the output path
        directory = await gazu.files.build_entity_output_file_path(
            entity, output_type, task_type, sep=os.path.sep
        )
        temp_directory = os.path.join(os.path.dirname(directory), str(uuid.uuid4()))
        file_name = directory.split(os.path.sep)[-1]
        return {
            "directory": directory,
            "file_name": file_name,
            "temp_directory": temp_directory,
        }
