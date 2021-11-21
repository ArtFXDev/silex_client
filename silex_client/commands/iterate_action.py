from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.commands.insert_action import InsertAction
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import ListParameterMeta, AnyParameter

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class IterateAction(InsertAction):
    """
    Execute an action over a given list
    """

    parameters = {
        "actions": {
            "label": "Action to execute",
            "type": ListParameterMeta(str),
            "value": None,
            "tooltip": "This action will be executed for each items in the given list",
        },
        "categories": {
            "label": "Action category",
            "type": ListParameterMeta(str),
            "value": "action",
            "tooltip": "Set the category of the action you want to execute",
        },
        "values": {
            "label": "List to iterate over",
            "type": ListParameterMeta(AnyParameter),
            "value": None,
            "tooltip": "A new action will be appended for each items in this list",
            "hide": True,
        },
        "parameter": {
            "label": "Parameters to set on the action",
            "type": str,
            "value": "",
            "tooltip": "Set wich parameter will be overriden by the item's value",
            "hide": True,
        },
        "label_key": {
            "label": "Value's key to set on the label",
            "type": str,
            "value": "",
            "tooltip": "If the value is a dictionary, the value at that key will be set on the label",
            "hide": True,
        },
        "output": {
            "label": "The command to get the output from",
            "type": str,
            "value": "",
            "tooltip": "The output of the given command will be returned",
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        actions = parameters["actions"]
        values = parameters["values"]
        categories = parameters["categories"]

        # Inherit from the parameters of the InsertAction command
        for key, value in super().parameters.items():
            value["name"] = key
            self.command_buffer.parameters.setdefault(key, ParameterBuffer(**value))

        outputs = []
        label = self.command_buffer.label
        for index, value in enumerate(values):
            self.command_buffer.label = f"{label} ({index+1}/{len(values)})"
            action = actions[index % len(actions)]
            category = categories[index % len(categories)]

            logger.info("Adding action %s for item %s", action, value)

            # Set the new values to the command
            parameters.update({"action": action, "value": value, "category": category})
            output = await super().__call__(upstream, parameters, action_query)
            outputs.append(output)

        return outputs
