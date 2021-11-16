from __future__ import annotations

import os
import uuid
import typing
import pathlib
from typing import Any, Dict

import fileseq
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
        "name": {
            "label": "Name",
            "type": str,
            "value": "",
        },
        "frame_set": {
            "label": "Insert the quantity of items if file sequence",
            "type": fileseq.FrameSet,
            "value": fileseq.FrameSet(0),
            "tooltip": "The range is start, end, increment",
        },
        "padding": {
            "label": "padding for index in sequences",
            "type": int,
            "value": 1,
            "hide": True,
            "tooltip": "A padding of 4 would return an index of 0024 for the index 24",
        },
    }

    required_metadata = ["entity_id", "task_type_id"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        create_output_dir: bool = parameters["create_output_dir"]
        create_temp_dir: bool = parameters["create_temp_dir"]
        name: str = parameters["name"]
        extension: str = parameters["output_type"]
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        padding: int = parameters["padding"]
        nb_elements = len(frame_set)

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
        output_path = await gazu.files.build_entity_output_file_path(
            entity, output_type, task_type, sep=os.path.sep, nb_elements=nb_elements
        )
        output_path = pathlib.Path(output_path)
        directory = output_path.parent
        temp_directory = directory / str(uuid.uuid4())
        file_name = output_path.name + f"_{name}" if name else output_path.name
        file_names = []
        full_paths = [directory / file_name]

        # Create the directories
        if create_output_dir:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Output directory created: {directory}")

        if create_temp_dir:
            os.makedirs(temp_directory)
            logger.info(f"Temp directory created: {temp_directory}")

        # Handle the sequences of files
        if nb_elements > 1:
            for item in frame_set:
                file_names.append(
                    file_name + f"_{str(item).zfill(padding)}.{extension}"
                )
            full_paths = [directory / name for name in file_names]
        else:
            file_names = file_name + f".{extension}"
            full_paths = directory / file_name

        logger.info("Output path(s) built: %s", full_paths)

        return {
            "directory": directory,
            "file_names": file_names,
            "temp_directory": temp_directory,
            "full_paths": full_paths,
        }
