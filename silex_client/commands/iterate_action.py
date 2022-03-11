from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.commands import insert_action
from silex_client.utils.parameter_types import AnyParameter, ListParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import importlib

importlib.reload(insert_action)


class IterateAction(insert_action.InsertAction):
    """
    Execute an action over a given list
    """

    parameters = {
        "actions": {
            "label": "Actions to execute",
            "type": ListParameterMeta(str),
            "value": None,
            "tooltip": "This action will be executed for each items in the given list",
        },
        "categories": {
            "label": "Action category",
            "type": ListParameterMeta(str),
            "value": "action",
            "tooltip": "Set the category of the action you want to execute",
            "hide": True,
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
        "hide_threshold": {
            "label": "Hide command threshold",
            "type": int,
            "value": 40,
            "tooltip": "If the number actions to add is superior to this threshold, the commands will be hidden",
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        actions = parameters["actions"]
        values = parameters["values"]
        categories = parameters["categories"]
        hide_threshold = parameters["hide_threshold"]

        outputs = []
        label = self.command_buffer.label

        hide_commands = len(values) > hide_threshold
        if hide_commands:
            label = f"{label} [optimized]"

        logger.info("Adding %s actions", len(values))
        for index, value in enumerate(values):
            self.command_buffer.label = f"{label} ({index+1}/{len(values)})"
            action = actions[index % len(actions)]
            category = categories[index % len(categories)]

            # Set the new values to the command
            parameters.update(
                {
                    "action": action,
                    "value": value,
                    "category": category,
                    "hide_commands": hide_commands,
                }
            )
            output = await super().__call__(parameters, action_query, logger)
            outputs.append(output)

        return outputs

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # Hide the parameters of the child classes
        for key, _ in super().parameters.items():
            parameter = self.command_buffer.parameters.get(key)
            if parameter is not None:
                parameter.hide = True
