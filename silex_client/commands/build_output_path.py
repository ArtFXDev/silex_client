from __future__ import annotations

import logging
import os
import pathlib
import typing
import uuid
from typing import Any, Dict, Optional

import fileseq
import gazu.asset
import gazu.files
import gazu.shot
import gazu.task
from silex_client.action.command_base import CommandBase
from silex_client.utils.files import slugify
from silex_client.utils.parameter_types import (
    SelectParameterMeta,
    StringParameterMeta,
    TaskParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPath(CommandBase):
    """
    Build the path where the output files should be saved to
    """

    parameters = {
        "use_existing_name": {
            "label": "Use existing published filename",
            "type": bool,
            "value": False,
            "tooltip": "Replaced the name parameter by a drop down of all the exising names",
        },
        "name": {
            "label": "Filename",
            "type": StringParameterMeta(max_lenght=40),
            "value": "",
            "tooltip": "This value can be left empty",
        },
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
        "frame_set": {
            "label": "Insert the quantity of items if file sequence",
            "type": fileseq.FrameSet,
            "value": fileseq.FrameSet(0),
            "tooltip": "The range is start, end, increment",
            "hide": True,
        },
        "padding": {
            "label": "padding for index in sequences",
            "type": int,
            "value": 1,
            "hide": True,
            "tooltip": "A padding of 4 would return an index of 0024 for the index 24",
        },
        "use_current_context": {
            "label": "output the given file to the current context",
            "type": bool,
            "value": True,
            "tooltip": "This parameter will overrite the select conform location",
        },
        "task": {
            "label": "Task",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Select the task where you can to conform your file",
        },
    }

    async def _get_existing_names(self, task_id, output_type, nb_elements):
        # Get the selected task an populate the existing name
        output_path = await self._get_gazu_output_path(
            task_id, output_type, nb_elements
        )
        if output_path is not None and output_path.parent.exists():
            return [str(s.name) for s in output_path.parent.iterdir() if s.is_dir()]
        else:
            return []

    @staticmethod
    async def _get_gazu_output_path(
        task_id: str, output_type: str, nb_elements: int
    ) -> Optional[pathlib.Path]:
        # Override with the given task if specified
        if task_id is None:
            return None
        task = await gazu.task.get_task(task_id)
        task_name = task["name"]
        entity = task.get("entity", {}).get("id")
        task_type = task.get("task_type", {}).get("id")

        # Get the output type
        output_type = await gazu.files.get_output_type_by_short_name(output_type)
        if output_type is None:
            raise Exception(
                f"Could not build the output type {output_type}: The output type does not exists in the zou database",
            )

        # Build the output path
        output_path = await gazu.files.build_entity_output_file_path(
            entity,
            output_type,
            task_type,
            sep=os.path.sep,
            nb_elements=nb_elements,
            name=task_name,
        )
        return pathlib.Path(output_path)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        create_output_dir: bool = parameters["create_output_dir"]
        create_temp_dir: bool = parameters["create_temp_dir"]
        use_current_context: bool = parameters["use_current_context"]
        output_type: str = parameters["output_type"]
        name: str = parameters["name"]
        task_id: str = parameters["task"]
        extension: str = parameters["output_type"]
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        padding: int = parameters["padding"]
        nb_elements = len(frame_set)

        if use_current_context:
            task_id = action_query.context_metadata["task_id"]

        output_path = await self._get_gazu_output_path(
            task_id, output_type, nb_elements
        )
        if output_path is None:
            raise Exception("Could not get the output path from gazu")

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
            "task": str(task_id),
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
        # Slugify the name
        name_parameter = self.command_buffer.parameters["name"]
        name_value = name_parameter.get_value(action_query)
        name_parameter.value = slugify(str(name_value))

        # This action can be used with or without a context
        for context_value in ["entity_id", "task_type_id", "entity_type", "task"]:
            if context_value not in action_query.context_metadata.keys():
                parameters["use_current_context"] = False
                self.command_buffer.parameters["use_current_context"].value = False
                self.command_buffer.parameters["use_current_context"].hide = True

        task_parameter = self.command_buffer.parameters["task"]

        # Set the hide dynamically
        task_parameter.hide = parameters.get("use_current_context", False)
        task_parameter.value = task_parameter.get_value(action_query)

        # Change the type of the name parameter is use_existing_name is true
        use_existing_name_parameter = self.command_buffer.parameters[
            "use_existing_name"
        ]
        if not use_existing_name_parameter.get_value(action_query):
            name_parameter.type = StringParameterMeta(max_lenght=40)
        else:
            use_current_context: bool = parameters["use_current_context"]
            task_id: str = parameters["task"]
            output_type: str = parameters["output_type"]
            frame_set: fileseq.FrameSet = parameters["frame_set"]
            nb_elements = len(frame_set)

            if use_current_context:
                task_id = action_query.context_metadata["task_id"]

            existing_names = await self._get_existing_names(
                task_id, output_type, nb_elements
            )
            if existing_names:
                name_parameter.type = SelectParameterMeta(*existing_names)
            else:
                name_parameter.type = SelectParameterMeta(**{"<no_name>": ""})
