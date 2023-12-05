from __future__ import annotations

import logging
import pathlib
import typing
import copy
from typing import Any, Dict

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.commands.build_output_path import BuildOutputPath
from silex_client.utils.parameter_types import PathParameterMeta, TextParameterMeta
from silex_client.action.parameter_buffer import ParameterBuffer
from pprint import pprint

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

    async def prompt_warning(self, action_query: ActionQuery, parameters):
        warning_parameter = ParameterBuffer(
            type=TextParameterMeta(color="warning"),
            value=(
                "WARNING: \n"
                + "The current name "
                + "Will override an existing conform\n"
                + "If you don't want to override previous conform "
                + "make sure to set a different name\n"
                + "Otherwise you can just press continue"
            ),
        )
        name_parameter = copy.copy(self.command_buffer.parameters["name"])
        task_parameter = copy.copy(self.command_buffer.parameters["task"])
        use_current_context_parameter = copy.copy(
            self.command_buffer.parameters["use_current_context"]
        )
        task_parameter.hide = False
        use_current_context_parameter.hide = False
        parameters["warning"] = warning_parameter

        response = await self.prompt_user(
            action_query,
            {
                "warning": warning_parameter,
                "name": name_parameter,
                "task": task_parameter,
                "use_current_context": use_current_context_parameter,
            },
        )
        for key, value in response.items():
            parameters[key] = value

        return response

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        fast_conform = parameters["fast_conform"]
        file_paths = fileseq.findSequencesInList(parameters["files"])[0]

        input_key = f"build_output_path_conform:{str(file_paths)}"
        result = await super().__call__(parameters, action_query, logger)
        result.update({"fast_conform": fast_conform})

        # When is enabled, files might be overriden, since the name is autofilled
        # To prevent this, we store the input directory and the output directory
        # and check if we are not building a path that has already been built
        action_query.store.setdefault("build_conform_path:output", [])
        if (
            action_query.store.get(f"fast_conform_enabled:{file_paths.dirname()}")
            and result["directory"] in action_query.store["build_conform_path:output"]
            and input_key not in action_query.store.keys()
        ):
            await self.prompt_warning(action_query, parameters)
            result.update(await super().__call__(parameters, action_query, logger))

        # Store the result of the built output path
        action_query.store["build_conform_path:output"].append(result["directory"])
        fast_conform_key = f"fast_conform_enabled:{file_paths.dirname()}"
        action_query.store[fast_conform_key] = (
            action_query.store.get(fast_conform_key) or fast_conform
        )
        action_query.store[input_key] = result

        result["store_conform_key"] = input_key
        # print(self.command_buffer.parameters["task"])
        # print(self.command_buffer.parameters["task"].value)
        
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
        if not name_parameter.get_value(action_query):
            name_parameter.value = new_name_value

        # Force the name to be visible
        self.command_buffer.parameters["name"].hide = False

        # If the fast_conform is enabled and a valid task is selected
        # Don't prompt the user
        task_parameter = self.command_buffer.parameters["task"]
        task_value = task_parameter.get_value(action_query)
        fast_conform = action_query.store.get(
            f"fast_conform_enabled:{file_paths.dirname()}"
        )
        current_status = self.command_buffer.status
        if (
            task_value is not None
            and fast_conform
            and current_status != 2
            and len(name_parameter.get_value(action_query)) < 40
        ):
            self.command_buffer.ask_user = False

        await super().setup(parameters, action_query, logger)
