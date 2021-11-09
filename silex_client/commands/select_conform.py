from __future__ import annotations
from silex_client.utils.datatypes import CommandOutput

import jsondiff
import copy
import os
import pathlib
import typing
import uuid
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.resolve.config import Config

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectConform(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "file_path": {
            "label": "Insert the file to conform",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Insert the path to the file you want to conform",
        },
        "auto_select_type": {
            "label": "Auto select the conform type",
            "type": bool,
            "value": True,
            "tooltip": "Guess the conform type from the extension",
        },
        "conform_type": {
            "label": "Select a conform type",
            "type": SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config().conforms]
            ),
            "value": None,
            "tooltip": "Select a conform type in the list",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        conform_type = parameters["conform_type"]
        if parameters["auto_select_type"]:
            extension = os.path.splitext(parameters["file_path"])[-1][1:]
            conform_type = extension.lower()
            # Some extensions are not the exact same as their conform type
            if conform_type not in [
                publish_action["name"] for publish_action in Config().conforms
            ]:
                # TODO: This mapping
                EXTENSION_TYPES_MAPPING = {"mb": "ma", "jpg": "jpeg"}
                # Find the right conform action for the given extension
                conform_type = EXTENSION_TYPES_MAPPING.get(conform_type)

            # Some extensions are just not handled at all
            if conform_type is None:
                raise Exception(
                    "Could not guess the conform for the selected file: The extension %s does not match any conform",
                    extension,
                )

        return {"type": conform_type, "file_path": parameters["file_path"]}
