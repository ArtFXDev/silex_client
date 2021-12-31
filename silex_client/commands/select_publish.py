from __future__ import annotations

import jsondiff
import typing
from typing import Any, Dict

import logging
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.resolve.config import Config

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
        publish_action = Config.get().resolve_publish(
            parameters["publish_type"].lower()
        )

        if publish_action is None:
            raise Exception("Could not resolve the action %s")

        # Make sure the required action is in the config
        if parameters["publish_type"] not in publish_action.keys():
            raise Exception(
                "Could not resolve the action {}: The root key should be the same as the config file name".format(
                    parameters["publish_type"]
                )
            )

        action_definition = publish_action[parameters["publish_type"]]
        action_definition["name"] = parameters["publish_type"]

        last_index = action_query.steps[-1].index
        if "steps" in action_definition and isinstance(
            action_definition["steps"], dict
        ):
            for step_value in action_definition["steps"].values():
                step_value["index"] = step_value.get("index", 10) + last_index

        patch = jsondiff.patch(action_query.buffer.serialize(), action_definition)
        action_query.buffer.deserialize(patch)
        return parameters["publish_type"]
