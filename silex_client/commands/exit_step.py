from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import Status

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
        "goto": {
            "label": "Name of the step to go to",
            "type": str,
            "value": "",
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
        goto: str = parameters["goto"]

        if not enable:
            return

        current_step_index = None
        goto_step_index = None
        for index, step in enumerate(action_query.steps):
            if self.command_buffer in step.children.values():
                current_step_index = index
                if not goto:
                    goto_step_index = index + 1
            if step.name == goto:
                goto_step_index = index

        if current_step_index is None:
            raise Exception("Could not find the current step")

        for step in action_query.steps[current_step_index:goto_step_index]:
            for command in step.children.values():
                if command.status is Status.COMPLETED:
                    continue
                command.skip = True
