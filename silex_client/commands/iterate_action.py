from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.commands.insert_action import InsertAction

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class IterateAction(InsertAction):
    """
    Execute an action over a given list
    """

    parameters = {
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
        "list": {
            "label": "List to iterate over",
            "type": list,
            "value": None,
            "tooltip": "A new action will be appended for each items in this list",
            "hide": True,
        },
        "value": {
            "label": "Value to set on the new action",
            "type": str,
            "value": "",
            "tooltip": "This value will be append to action's steps labels",
            "hide": True,
        },
        "parameter": {
            "label": "Parameters to set on the action",
            "type": str,
            "value": "",
            "tooltip": "Set wich parameter will be overriden by the item's value",
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
        outputs = []
        for value in parameters["list"]:
            logger.info("Adding action %s for item %s", parameters["action"], value)
            self.command_buffer.parameters["value"].value = value
            parameters["value"] = value
            await super().__call__(upstream, parameters, action_query)
            # TODO: Figure out why tf the returned value is always None
            outputs.append(self._transfer_data)

        return outputs
