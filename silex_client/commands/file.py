from __future__ import annotations

import os
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class PublishFile(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": str,
            "value": None,
            "tooltip": "The path to the file you want to publish",
        },
        "description": {
            "label": "Description",
            "type": str,
            "value": "No description",
            "tooltip": "Short description of your work",
        },
    }

    required_metadata = ["project"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        publish_path = os.path.join(
            action_query.context_metadata["project"], parameters["name"]
        )

        logger.info(
            "Publishing file(s) %s to %s", parameters["file_path"], publish_path
        )

        return publish_path
