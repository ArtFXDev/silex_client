from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.commands.build_output_path import BuildOutputPath

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPathConform(BuildOutputPath):
    """
    BuildOutputPath with extra features to auto complete the parameters
    """

    parameters = {
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
        result = await super().__call__(parameters, action_query, logger)
        result.update({"fast_conform": fast_conform})
        return result

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        await super().setup(parameters, action_query, logger)

        # If the fast_conform is enabled and a valid task is selected
        # Don't prompt the user
        task_parameter = self.command_buffer.parameters["task"]
        fast_parameter = self.command_buffer.parameters["fast_conform"]
        fast_conform = fast_parameter.get_value(action_query)
        if task_parameter.get_value(action_query) is not None and fast_conform:
            self.command_buffer.ask_user = False
        else:
            fast_parameter.hide = False
