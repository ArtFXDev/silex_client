from __future__ import annotations

import typing
from typing import Any, Dict
import logging

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import AnyParameter

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Pass(CommandBase):
    """
    This command does nothing, it is used to pass a value from an action to an other
    """

    parameters = {
        "input": {
            "type": AnyParameter,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        return parameters["input"]
