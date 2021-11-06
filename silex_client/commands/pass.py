from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Pass(CommandBase):
    """
    This command does nothing, it is used to pass a value from an action to an other
    """

    parameters = {
        "input": {
            "type": str,
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        return parameters["input"]
