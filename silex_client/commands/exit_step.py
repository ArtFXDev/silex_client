from __future__ import annotations

import logging
import typing
from typing import Any, cast, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import Status

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.step_buffer import StepBuffer


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

        current_step = cast("StepBuffer", self.command_buffer.parent)
        current_step_index = action_query.steps.index(current_step)
        goto_step_index = None

        if goto:
            for index, step in enumerate(action_query.steps[current_step_index:]):
                if step.name == goto:
                    goto_step_index = index
        else:
            goto_step_index = current_step_index + 1

        for step in action_query.steps[current_step_index:goto_step_index]:
            for command in step.children.values():
                if command.status is Status.COMPLETED:
                    continue
                command.skip = True
