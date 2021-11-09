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
from silex_client.utils.parameter_types import TaskParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPath(CommandBase):
    """
    Build the path where the output files should be saved to
    """

    parameters = {
        "output_type": {
            "label": "Insert publish type",
            "type": str,
            "value": None,
            "tooltip": "Insert the short name of the output type",
        },
        "create_temp_dir": {
            "label": "Create temp directory",
            "type": bool,
            "value": True,
            "hide": True,
        },
        "create_output_dir": {
            "label": "Create output directory",
            "type": bool,
            "value": True,
            "hide": True,
        },
        "use_current_context": {
            "label": "Conform the given file to the current context",
            "type": bool,
            "value": True,
            "tooltip": "This parameter will overrite the select conform location",
        },
        "task": {
            "label": "Select conform location",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Select the task where you can to conform your file",
        },
    }

    required_metadata = ["entity_id", "task_type_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        # f/p
        create_output_dir = parameters["create_output_dir"]
        create_temp_dir = parameters["create_temp_dir"]

        # Get the entity dict
        entity = await gazu.shot.get_shot(action_query.context_metadata["entity_id"])

        # Get the output type
        output_type = await gazu.files.get_output_type_by_short_name(
            parameters["output_type"]
        )
        if output_type is None:
            logger.error(
                "Could not build the output type %s: The output type does not exists in the zou database",
                parameters["output_type"],
            )
            raise Exception(
                "Could not build the output type %s: The output type does not exists in the zou database",
                parameters["output_type"],
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

        # Override with the given task if specified
        if not parameters["use_current_context"]:
            task = await gazu.task.get_task(parameters["task"])
            entity = task.get("entity", {}).get("id")
            task_type = task.get("task_type", {}).get("id")

        # Build the output path
        directory = await gazu.files.build_entity_output_file_path(
            entity, output_type, task_type, sep=os.path.sep
        )
        file_name = os.path.basename(directory)
        directory = os.path.dirname(directory)

        if create_output_dir:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Output directory created: {directory}")

        temp_directory = os.path.join(os.path.dirname(directory), str(uuid.uuid4()))
        if create_temp_dir:
            os.makedirs(temp_directory)
            logger.info(f"Temp directory created: {temp_directory}")

        file_name = os.path.basename(directory)
        logger.info("Output path built: %s", os.path.join(directory, file_name))
        return {
            "directory": directory,
            "file_name": file_name,
            "temp_directory": temp_directory,
            "full_path": f"{os.path.join(directory, file_name)}.{parameters['output_type']}",
        }
