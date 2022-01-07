from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Log(CommandBase):
    """
    Log the given string
    """

    parameters = {
        "message": {"label": "Message", "type": str, "value": None},
        "level": {"label": "Level", "type": str, "value": "info"},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        try:
            getattr(logger, parameters["level"])(parameters["message"])
        except ValueError:
            logger.warning("Invalid log level")
