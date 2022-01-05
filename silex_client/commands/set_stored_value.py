from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import AnyParameter
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetStoredValue(CommandBase):
    """
    Store a given value into the action's global store
    """

    parameters = {
        "key": {
            "label": "Key",
            "type": str,
            "value": None,
            "hide": True,
        },
        "value": {
            "label": "Value",
            "type": AnyParameter,
            "value": None,
            "hide": True,
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
        value: Any = parameters["value"]

        action_query.store[key] = value
        return {"value": value, "key": key}
