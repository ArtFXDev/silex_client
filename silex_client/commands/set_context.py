from __future__ import annotations

import os
import logging
import typing
from typing import Any, Dict

from silex_client.core.context import Context
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TaskParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetContext(CommandBase):
    """
    Set the context of the current session
    """

    parameters = {
        "task": {
            "label": "Select conform location",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Select the task where you can to conform your file",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        task_id: str = parameters["task"]
        os.environ["SILEX_TASK_ID"] = task_id
        Context.get().compute_metadata()
