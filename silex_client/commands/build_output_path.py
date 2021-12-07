from __future__ import annotations

import os
import uuid
import typing
import pathlib
import re
from typing import Any, Dict

import fileseq
import gazu.shot
import gazu.asset
import gazu.files
import gazu.task

from silex_client.action.command_base import CommandBase
import logging
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
            "label": "output the given file to the current context",
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

    required_metadata = ["entity_id", "task_type_id", "entity_type", "task"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        create_output_dir: bool = parameters["create_output_dir"]
        create_temp_dir: bool = parameters["create_temp_dir"]
        name: str = parameters["name"]
        extension: str = parameters["output_type"]
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        padding: int = parameters["padding"]
        nb_elements = len(frame_set)

        # Get the entity dict
        entity = None
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

        # Get the task name
        task_name = action_query.context_metadata["task"]

        # Override with the given task if specified
        if not parameters["use_current_context"]:
            task = await gazu.task.get_task(parameters["task"])
            task_name = task["name"]
            entity = task.get("entity", {}).get("id")
            task_type = task.get("task_type", {}).get("id")

        # Build the output path
        output_path = await gazu.files.build_entity_output_file_path(
            entity, output_type, task_type, sep=os.path.sep, nb_elements=nb_elements, name=task_name
        )
        output_path = pathlib.Path(output_path)

        directory = output_path.parent / name if name else output_path.parent
        temp_directory = output_path.parent / str(uuid.uuid4())
        file_name = output_path.name + f"_{name}" if name else output_path.name
        full_name = file_name
        full_names = []
        full_paths = [directory / full_name]

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
                full_names.append(
                    full_name + f".{str(item).zfill(padding)}.{extension}"
                )
            full_paths = [directory / name for name in full_names]
        else:
            full_names = full_name + f".{extension}"
            full_paths = directory / full_names

        if isinstance(full_paths, list):
            sequence = fileseq.findSequencesInList(full_paths)
            logger.info("Output path(s) built: %s", sequence)
        else:
            logger.info("Output path(s) built: %s", full_paths)

        return {
            "directory": directory,
            "file_name": file_name,
            "full_name": full_names,
            "temp_directory": temp_directory,
            "full_path": full_paths,
            "frame_set": frame_set,
        }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Handle the case where a file sequence is given
        name_value = self.command_buffer.parameters["name"].get_value(action_query)
        sequences = []
        new_value = name_value
        if isinstance(name_value, list):
            sequences = fileseq.findSequencesInList(name_value)
            new_value = sequences[0].basename()
        elif name_value:
            new_value = pathlib.Path(str(name_value)).stem

        new_value = re.sub(r"^\W+|\W+$", "", new_value).strip("_")
        self.command_buffer.parameters["name"].value = new_value

        # Force the name to be visible
        self.command_buffer.parameters["name"].hide = False
