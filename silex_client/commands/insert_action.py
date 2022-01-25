from __future__ import annotations

import copy
import logging
import typing
from typing import Any, Dict
import uuid

import fileseq

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.parameter_types import AnyParameter

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class InsertAction(CommandBase):
    """
    Insert an action's steps after the current step
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
        "value": {
            "label": "Value to set on the new action",
            "type": AnyParameter,
            "value": "",
            "tooltip": "This value will be append to action's steps labels",
            "hide": True,
        },
        "parameter": {
            "label": "Parameters to set on the action",
            "type": str,
            "value": "",
            "tooltip": "Set wich parameter will be overriden by the given value",
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
        "hide_commands": {
            "label": "Hide the insterted commands",
            "type": bool,
            "value": False,
            "tooltip": "This option is for performance purpose",
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
        action_type = parameters["action"]
        label_key = parameters["label_key"]
        value = parameters["value"]
        parameter = parameters["parameter"]
        hide_commands = parameters["hide_commands"]

        resolved_action = Config.get().resolve_action(
            action_type, parameters["category"]
        )

        if resolved_action is None:
            raise Exception(f"Could not resolve the action {action_type}")

        # Make sure the required action is in the config
        if action_type not in resolved_action.keys():
            raise Exception(
                f"Could not resolve the action {action_type}: The root key should be the same as the config file name"
            )

        action_name = f"action_type_{uuid.uuid4()}"
        action_definition = resolved_action[action_type]
        action_definition["name"] = action_name
        action_definition["buffer_type"] = "actions"

        current_action = self.command_buffer.get_parent("actions")
        current_step = self.command_buffer.get_parent("steps")
        if current_action is None or current_step is None:
            raise Exception(
                "Could not append new action: The current command is invalid"
            )

        current_action_steps = list(current_action.children.values())
        current_step_index = current_action_steps.index(current_step)
        next_steps = current_action_steps[current_step_index + 1 :]
        index_shift = action_definition.get("index", 0) + 1

        action_definition["index"] = current_step.index + index_shift

        for next_step in next_steps:
            next_step.index += index_shift

        # Apply the new action to the current action
        logger.info("Inserting action: %s", action_name)
        current_action.deserialize({"actions": {action_name: action_definition}})
        inserted_action: ActionBuffer = current_action.children[action_name]

        # Set the parameter at the given path to the given value
        if parameter:
            inserted_action.set_parameter(parameter.split(":"), value)
        # The user can hide the commands, because the actions can get big when inserting actions
        if hide_commands or self.command_buffer.hide or action_query.buffer.simplify:
            for command in inserted_action.commands:
                command.hide = True
        # The label key is here to help differentiate
        # when the same action is inserted multiple times
        if label_key:
            splitter_label_key = label_key.split(":")
            label_value = copy.deepcopy(value)
            while isinstance(label_value, dict) and splitter_label_key:
                label_value = label_value.get(splitter_label_key[0])
                splitter_label_key.pop(0)
            if isinstance(label_value, list):
                label_value = fileseq.findSequencesInList(label_value)[0]
            inserted_action.label = f"{inserted_action.label}: {str(label_value)}"
