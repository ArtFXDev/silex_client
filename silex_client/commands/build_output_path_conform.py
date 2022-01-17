from __future__ import annotations

import logging
import typing
import pathlib
from typing import Any, Dict
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.commands.build_output_path import BuildOutputPath

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
        files_value = fileseq.findSequencesInList(files_value)[0]

        # If the file has already been conformed, don't build the path
        key = f"build_output_path_conform:{str(files_value)}"
        previous_result = action_query.store.get(key)
        if previous_result is not None:
            self.command_buffer.output_result = previous_result
            self.command_buffer.ask_user = False
            return

        # Autofill the name from the files
        new_name_value = files_value.basename()
        name_parameter = self.command_buffer.parameters["name"]
        name_parameter.value = new_name_value

        # Force the name to be visible
        self.command_buffer.parameters["name"].hide = False

        # If the fast_conform is enabled and a valid task is selected
        # Don't prompt the user
        task_parameter = self.command_buffer.parameters["task"]
        task_value = task_parameter.get_value(action_query)
        fast_parameter = self.command_buffer.parameters["fast_conform"]
        fast_conform = fast_parameter.get_value(action_query)
        current_status = self.command_buffer.status
        if task_value is not None and fast_conform and current_status != 2:
            self.command_buffer.ask_user = False
        else:
            fast_parameter.hide = False

        await super().setup(parameters, action_query, logger)
