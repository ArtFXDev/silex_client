from __future__ import annotations

import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import (
    SelectParameterMeta,
)
from silex_client.resolve.config import Config

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectSubmit(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "submiter": {
            "label": "Select a submiter",
            "type": SelectParameterMeta(
                *[submit_action["name"] for submit_action in Config().submits]
            ),
            "value": None,
            "tooltip": "Select a submiter in the list",
        },
    }

    async def _prompt_new_submit(self, action_query: ActionQuery) -> str:
        """
        Helper to prompt the user for a new submiter and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        new_parameter = ParameterBuffer(
            type=SelectParameterMeta(
                *[submit_action["name"] for submit_action in Config().submits]
            ),
            name="new_submit",
            label=f"Submiter",
        )
        # Prompt the user to get the new path
        new_submit = await self.prompt_user(
            action_query,
            {"new_submit": new_parameter},
        )
        return new_submit["new_submit"]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        submiter: str = parameters["submiter"]

        while submiter not in [submit_action["name"] for submit_action in Config().submits]:
            submiter = await self._prompt_new_submit(action_query)

        return {
            "action": submiter,
        }

