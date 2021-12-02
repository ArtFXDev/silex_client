from __future__ import annotations

import jsondiff
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
import logging
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import (
    SelectParameterMeta,
    ListParameterMeta,
    AnyParameter,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectList(CommandBase):
    """
    Prompt user for a custom list of parameters
    """

    parameters = {
        "parameters_list": {"type": ListParameterMeta(AnyParameter), "hide": True},
        "param_name": {"type": str, "hide": True},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        parameters_list: List[Any] = parameters.get("parameters_list")
        param_name: str = parameters.get("param_name")

        response: Dict[Any] = await self.prompt_user(
            action_query,
            {
                "selected_param": ParameterBuffer(
                    name="selected_param",
                    type=SelectParameterMeta(*parameters_list),
                    label=param_name,
                )
            },
        )
        return response.get("selected_param")
