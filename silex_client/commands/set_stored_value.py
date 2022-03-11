from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import AnyParameter, ListParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetStoredValue(CommandBase):
    """
    Store a given value into the action's global store
    """

    parameters = {
        "keys": {
            "label": "Key",
            "type": ListParameterMeta(str),
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
        keys: List[str] = parameters["keys"]
        value: Any = parameters["value"]

        store = action_query.store
        for key in keys[:-1]:
            if not isinstance(store, dict):
                break
            store = store.get(key)

        if not isinstance(store, dict):
            raise Exception(f"Could not set the value at {keys} in the store")

        store[keys[-1]] = value
        return {"value": value, "keys": keys}
