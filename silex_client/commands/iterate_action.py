from __future__ import annotations
import uuid

import jsondiff
import copy
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class IterateAction(CommandBase):
    """
    Execute an action over a given list
    """

    parameters = {
        "list": {
            "label": "List to iterate over",
            "type": list,
            "value": None,
            "tooltip": "A new action will be appended for each items in this list",
            "hide": True,
        },
        "action": {
            "label": "Action to execute",
            "type": str,
            "value": None,
            "tooltip": "This action will be executed for each items in the given list",
        },
        "parameter": {
            "label": "Parameters to set on the action",
            "type": str,
            "value": "",
            "tooltip": "Set wich parameter will be overriden by the item's value",
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        action_type = parameters["action"]
        action = Config().resolve_action(action_type)

        if action is None:
            raise Exception("Could not resolve the action %s", action_type)

        # Make sure the required action is in the config
        if action_type not in action.keys():
            raise Exception(
                "Could not resolve the action {}: The root key should be the same as the config file name".format(
                    action_type
                )
            )

        for item in parameters["list"]:
            logger.info("Adding action %s for item %s", action_type, item)
            parameter_path = parameters["parameter"].split(":")
            action_definition = copy.deepcopy(action[action_type])
            action_definition["name"] = action_type

            last_index = action_query.steps[-1].index
            if "steps" in action_definition and isinstance(
                action_definition["steps"], dict
            ):
                for step_name, step_value in action_definition["steps"].items():
                    step_value["index"] = step_value.get("index", 10) + last_index
                    step_value["label"] = step_value.get("label", step_name.title())
                    step_value["label"] += f" {item}"

                for step_name in copy.copy(list(action_definition["steps"].keys())):
                    new_name = step_name + "_" + str(uuid.uuid4())
                    action_definition["steps"][new_name] = action_definition[
                        "steps"
                    ].pop(step_name)
                    if parameter_path[0] == step_name:
                        parameter_path[0] = new_name

            patch = jsondiff.patch(action_query.buffer.serialize(), action_definition)
            action_query.buffer.deserialize(patch)
            logger.info(parameter_path)
            if parameters["parameter"]:
                action_query.set_parameter(":".join(parameter_path), item, hide=True)
