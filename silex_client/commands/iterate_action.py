from __future__ import annotations
import uuid

import jsondiff
import copy
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.log import logger
from silex_client.utils.datatypes import CommandOutput

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
        "category": {
            "label": "Action category",
            "type": str,
            "value": "action",
            "tooltip": "Set the category of the action you want to execute",
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
        action = Config().resolve_action(action_type, parameters["category"])

        if action is None:
            raise Exception("Could not resolve the action %s", action_type)

        # Make sure the required action is in the config
        if action_type not in action.keys():
            raise Exception(
                "Could not resolve the action {}: The root key should be the same as the config file name".format(
                    action_type
                )
            )

        resolved_action_definition = action[action_type]
        resolved_action_definition["name"] = action_type
        if not isinstance(resolved_action_definition.get("steps"), dict):
            raise Exception(
                "Could not append new action: The resolved action has not steps"
            )

        for item in parameters["list"]:
            logger.info("Adding action %s for item %s", action_type, item)
            action_definition = copy.deepcopy(resolved_action_definition)
            action_steps = action_definition.get("steps")
            parameter_path = parameters["parameter"].split(":")

            # Rename each steps to make sure they don't override existing steps
            step_name_mapping = {name: name for name in list(action_steps.keys())}
            for step_name in step_name_mapping.keys():
                new_name = step_name + "_" + str(uuid.uuid4())
                step_name_mapping[step_name] = new_name
                action_steps[step_name].setdefault("label", step_name.title())
                action_steps[step_name]["label"] = (
                    action_steps[step_name]["label"] + " : " + str(item)
                )
                action_steps[new_name] = action_steps.pop(step_name)
                if parameter_path[0] == step_name:
                    parameter_path[0] = new_name

            # Edit the steps to avoid conflict when they will be merged with the current action
            last_index = action_query.steps[-1].index
            for step_name, step_value in action_definition["steps"].items():
                step_value["index"] = step_value.get("index", 10) + last_index

                # TODO: Refactor this mess
                for command in step_value.get("commands", {}).values():
                    for parameter_name, parameter in command.get(
                        "parameters", {}
                    ).items():
                        if not isinstance(parameter, CommandOutput):
                            continue

                        parameter_split = parameter.split(":")
                        if parameter_split[0] in step_name_mapping.keys():
                            parameter_split[0] = step_name_mapping[parameter_split[0]]
                            command["parameters"][parameter_name] = CommandOutput(
                                ":".join(parameter_split)
                            )

            patch = jsondiff.patch(action_query.buffer.serialize(), action_definition)
            action_query.buffer.deserialize(patch)
            if parameters["parameter"]:
                action_query.set_parameter(":".join(parameter_path), item, hide=True)
