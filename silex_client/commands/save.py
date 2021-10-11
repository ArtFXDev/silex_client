from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Save(CommandBase):
    """
    Save current scene with context as path
    """

    parameters = {
        "filename": { "label": "filename", "type": str, "value": "", "hide": True }
    }


    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        print(action_query.context_metadata)
        pass