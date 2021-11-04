from __future__ import annotations

import jsondiff
import os
import pathlib
import typing
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
        "conform_type": {
            "label": "Select a conform type",
            "type": SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config().conforms]
            ),
            "value": None,
            "tooltip": "Select a conform type in the list",
        },
        "auto_select_type": {
            "label": "Auto select the conform type",
            "type": bool,
            "value": True,
            "tooltip": "Guess the conform type from the extension",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        conform_type = parameters["conform_type"]
        if parameters["auto_select_type"]:
            conform_type = os.path.splitext(parameters["file_path"])[-1][1:]

        conform_action = Config().resolve_conform(conform_type)

        if conform_action is None:
            raise Exception("Could not resolve the action %s")

        # Make sure the required action is in the config
        if conform_type not in conform_action.keys():
            raise Exception(
                "Could not resolve the action {}: The root key should be the same as the config file name".format(
                    parameters["publish_type"]
                )
            )

        action_definition = conform_action[conform_type]
        action_definition["name"] = conform_type

        last_index = action_query.steps[-1].index
        if "steps" in action_definition and isinstance(
            action_definition["steps"], dict
        ):
            for step_value in action_definition["steps"].values():
                step_value["index"] = step_value.get("index", 10) + last_index

        patch = jsondiff.patch(action_query.buffer.serialize(), action_definition)
        action_query.buffer.deserialize(patch)
        return conform_type
