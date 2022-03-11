from __future__ import annotations

import logging
import typing
from typing import Any, cast, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import Status

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.step_buffer import StepBuffer


class GoToStep(CommandBase):
    """
    Exit the selected steps by setting all its commands to skip
    The step can be selected by name or by count. If no name is specified, the count
    is used.
    """

    parameters = {
        "name": {
            "label": "Name of the step to go to",
            "type": str,
            "value": "",
        },
        "count": {
            "type": int,
            "label": "Quantity of step to skip",
            "tooltip": "The count start at the current step, (1 will skip the current step)",
            "value": 1,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        name: str = parameters["name"]
        count: int = parameters["count"]

        current_step = cast("StepBuffer", self.command_buffer.parent)
        current_step_index = action_query.steps.index(current_step)

        goto_step_index = current_step_index + count
        if name:
            for index, step in enumerate(action_query.steps[current_step_index:]):
                if name and step.name == name:
                    goto_step_index += index

        for step in action_query.steps[current_step_index:goto_step_index]:
            for command in step.children.values():
                if command.status is Status.COMPLETED:
                    continue
                command.skip = True
