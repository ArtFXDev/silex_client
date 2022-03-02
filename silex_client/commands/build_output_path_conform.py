from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.commands.build_output_path import BuildOutputPath
from silex_client.utils.parameter_types import PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPathConform(BuildOutputPath):
    """
    BuildOutputPath with extra features to auto complete the parameters
    """

    parameters = {
        "files": {
            "label": "File paths the we want to conform",
            "type": PathParameterMeta(multiple=True),
            "hide": True,
        },
        "fast_conform": {
            "label": "Fast conform the next files in this directory",
            "type": bool,
            "value": False,
            "tooltip": "All the files in this directory will be conform in the selected location without any prompt",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        fast_conform = parameters["fast_conform"]
        file_paths = parameters["files"]

        result = await super().__call__(parameters, action_query, logger)
        result.update({"fast_conform": fast_conform})

        # Store the result of the built output path
        file_paths = fileseq.findSequencesInList(file_paths)[0]
        key = f"build_output_path_conform:{str(file_paths)}"
        action_query.store[key] = result

        result["store_conform_key"] = key
        return result

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        files_parameter = self.command_buffer.parameters["files"]
        files_value = files_parameter.get_value(action_query)
        if not isinstance(files_value, list):
            files_value = [files_value]
        file_paths: fileseq.FileSequence = fileseq.findSequencesInList(files_value)[0]

        # If the file has already been conformed, don't build the path
        key = f"build_output_path_conform:{str(file_paths)}"
        previous_result = action_query.store.get(key)
        if previous_result is not None:
            self.command_buffer.output_result = previous_result
            self.command_buffer.skip = True
            return

        # Autofill the name from the files
        new_name_value = file_paths.basename()
        if len(file_paths) <= 1:
            new_name_value = pathlib.Path(str(file_paths[0])).stem
        name_parameter = self.command_buffer.parameters["name"]
        warning_parameter = self.command_buffer.parameters["info"]
        if not name_parameter.get_value(action_query):
            name_parameter.value = new_name_value
        name_value = name_parameter.get_value(action_query)

        # Force the name to be visible
        self.command_buffer.parameters["name"].hide = False

        warning_parameter.hide = True
        use_existing_name: bool = parameters["use_existing_name"]
        task_id: str = parameters["task"]
        output_type: str = parameters["output_type"]
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        nb_elements = len(frame_set)
        existing_names = await self._get_existing_names(
            task_id, output_type, nb_elements
        )
        if not use_existing_name and name_value in existing_names:
            warning_parameter.rebuild_type(color="info")
            warning_parameter.value = (
                "WARNING: \n"
                + "The current name "
                + "Will override an existing conform"
                + "If you don't want to override previous conform "
                + "make sure to set a different name"
            )
            warning_parameter.hide = False

        if len(name_value) > 40:
            warning_parameter.rebuild_type(color="warning")
            warning_parameter.value = (
                "WARNING: \n"
                + "The autofilled name is too long. "
                + "Make sure to enter a name with less that 40 characters "
                + "otherwise the name will be clamped"
            )
            warning_parameter.hide = False

        # If the fast_conform is enabled and a valid task is selected
        # Don't prompt the user
        task_parameter = self.command_buffer.parameters["task"]
        task_value = task_parameter.get_value(action_query)
        fast_parameter = self.command_buffer.parameters["fast_conform"]
        fast_conform = fast_parameter.get_value(action_query)
        current_status = self.command_buffer.status
        if (
            task_value is not None
            and fast_conform
            and current_status != 2
            and warning_parameter.hide
        ):
            self.command_buffer.ask_user = False

        fast_parameter.hide = False
        await super().setup(parameters, action_query, logger)
