from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class ExitStep(CommandBase):
    """
    Exit the current step by setting all the commands to skip
    """

    parameters = {
        "enable": {
            "label": "Enable the skip",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        enable: bool = parameters["enable"]

        if not enable:
            return

        current_step = None
        for step in action_query.steps:
            if self.command_buffer in step.children.values():
                current_step = step
                break

        if current_step is None:
            raise Exception("Could not find the current step")

        for command in current_step.children.values():
            command.skip = True
