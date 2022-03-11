from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import AnyParameter, ListParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GetStoredValue(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "keys": {
            "label": "Key",
            "type": ListParameterMeta(str),
        },
        "default": {
            "label": "Default value",
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
        keys: List[str] = parameters["keys"]
        default: Any = parameters["default"]

        value = action_query.store
        for key in keys:
            if not isinstance(value, dict):
                value = default
                break
            value = value.get(key, default)

        return {"value": value, "keys": keys}
