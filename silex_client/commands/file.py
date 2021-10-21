from __future__ import annotations

import os
import typing
import pathlib
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.utils.parameter_types import RangeParameterMeta

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
        "parameter_test": {
            "label": "Test",
            "type": RangeParameterMeta(1, 2),
            "value": 1,
            "tooltip": "Range",
        },
        "path": {
            "label": "Test",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Range",
        },
    }

    required_metadata = ["project"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        publish_path = os.path.join(
            action_query.context_metadata["project"], parameters["file_path"]
        )
        print(parameters["parameter_test"])
        print(type(parameters["parameter_test"]))

        logger.info(
            "Publishing file(s) %s to %s", parameters["file_path"], publish_path
        )

        return publish_path
