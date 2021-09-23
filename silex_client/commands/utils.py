from __future__ import annotations
import typing

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Log(CommandBase):
    """
    Log the given string
    """

    parameters = {
        "message": {
            "label": "Message",
            "type": str,
            "value": None
        },
        "level": {
            "label": "Level",
            "type": str,
            "value": "info"
        }
    }

    @CommandBase.conform_command()
    def __call__(self, parameters: dict, action_query: ActionQuery):
        try:
            getattr(logger, parameters["level"])(parameters["message"])
        except ValueError:
            logger.warning("Invalid log level")
