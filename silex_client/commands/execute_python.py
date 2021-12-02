from __future__ import annotations
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class ExecutePython(CommandBase):
    """
    Execute the given python code
    """

    parameters = {
        "inline_code": {
            "label": "Inline code",
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
        inline_code: str = parameters["inline_code"]

        return {"inline_result": eval(inline_code)}
