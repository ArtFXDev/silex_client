from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GetStoredValue(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "key": {
            "label": "Key",
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
        key: str = parameters["key"]

        value = action_query.store.get(key)
        return {"value": value, "key": key}
