from __future__ import annotations

import logging
import typing
from typing import Any, Dict

import jsondiff

from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.parameter_types import SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectPublish(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "publish_type": {
            "label": "Select a publish type",
            "type": SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config.get().publishes]
            ),
            "value": None,
            "tooltip": "Select a publish type in the list",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        return {"publish_type": parameters["publish_type"].lower()}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Set a default value
        publish_type = self.command_buffer.parameters["publish_type"]
        self.command_buffer.output_result = {
            "publish_type": publish_type.get_value(action_query)
        }
