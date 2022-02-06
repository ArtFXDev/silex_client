"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of the Log command
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from silex_client.action.command_definition import CommandDefinition
from silex_client.action.command_sockets import CommandSockets

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Log(CommandDefinition):
    """
    Log the given string
    """

    inputs = {
        "message": {"label": "Message", "type": str, "value": None},
        "level": {"label": "Level", "type": str, "value": "info"},
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        try:
            getattr(logger, parameters["level"])(parameters["message"])
        except ValueError:
            logger.warning("Invalid log level")
