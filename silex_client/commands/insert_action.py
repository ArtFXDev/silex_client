from __future__ import annotations

import copy
import logging
import typing
import uuid
from typing import Any, Dict

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.datatypes import CommandOutput
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
        hide_commands = parameters["hide_commands"]
        action = Config.get().resolve_action(action_type, parameters["category"])

        if action is None:
            raise Exception("Could not resolve the action %s", action_type)

        # Make sure the required action is in the config
        if action_type not in action.keys():
            raise Exception(
                "Could not resolve the action {}: The root key should be the same as the config file name".format(
                    action_type
                )
            )

        action_definition = action[action_type]
        action_definition["name"] = action_type
        if not isinstance(action_definition.get("steps"), dict):
            raise Exception(
                "Could not append new action: The resolved action has not steps"
            )

        action_steps = action_definition.get("steps")
        parameter_path = CommandOutput(parameters["parameter"])
        output_path = CommandOutput(parameters["output"])

        # Get the current step and the next step to insert the new steps in between
        current_step_index = next(
            index
            for index, step in enumerate(action_query.steps)
            if self.command_buffer in step.commands.values()
        )
        current_step = action_query.steps[current_step_index]
        next_steps = action_query.steps[current_step_index + 1 :]

        # Rename each steps to make sure they don't override existing steps
        step_name_mapping = {name: name for name in list(action_steps.keys())}
        for step_name in step_name_mapping.keys():
            new_name = step_name + ":" + str(uuid.uuid4())
            step_name_mapping[step_name] = new_name
            # Set the step label before applying it on the action query
            action_steps[step_name].setdefault("label", step_name.title())
            if value:
                # Add to the label the value to help differenciate it from others
                splitted_key = label_key.split(":") if label_key else []
                value_copy = copy.deepcopy(value)
                while isinstance(value_copy, dict) and splitted_key:
                    value_copy = value_copy.get(splitted_key[0])
                    splitted_key.pop(0)
                if isinstance(value_copy, list):
                    value_copy = fileseq.findSequencesInList(value_copy)[0]
                action_steps[step_name]["label"] = (
                    action_steps[step_name]["label"] + " : " + str(value_copy)
                )
            # Rename the step
            action_steps[new_name] = action_steps.pop(step_name)

        # Remove all the action's infos that are not about the steps
        for key in list(action_definition.keys()):
            if key != "steps":
                del action_definition[key]
        # Apply the new action to the current action
        # patch = jsondiff.patch(action_query.buffer.serialize(), action_definition)
        action_query.buffer.deserialize(action_definition)

        # Adapt the indexes, the parameter paths on the newly added steps
        last_index = current_step.index
        for old_step_name, step_name in step_name_mapping.items():
            step = action_query.buffer.steps[step_name]
            # Change the index to make sure the new step in executed after the current step
            step.index += current_step.index
            last_index = step.index

            # Adapt the parameter_path to the new step's name
            if parameter_path.step == old_step_name:
                parameter_path.step = step_name
            # Adapt the output_path to the new step's name
            if output_path.step == old_step_name:
                output_path.step = step_name

            # Loop over all the commands of the step
            if (
                action_query.buffer.simplify
                or hide_commands
                or self.command_buffer.hide
            ):
                for command in step.commands.values():
                    command.hide = True

            # Loop over all the parameters of the step
            step_parameters = [
                parameter
                for command in step.commands.values()
                for parameter in command.parameters.values()
                if isinstance(parameter.value, CommandOutput)
            ]
            for parameter in step_parameters:
                # If the parameter was pointing to a newly added step
                if parameter.value.step in step_name_mapping.keys():
                    # Make it point to the new name of the step
                    parameter.value.step = step_name_mapping[parameter.value.step]
                    parameter.value = parameter.value.rebuild()

        # Change the index of the steps that where after to maintain them after
        for step in next_steps:
            index_difference = step.index - current_step.index
            step.index = last_index + index_difference

        action_query.buffer.reorder_steps()

        if parameter_path:
            action_query.set_parameter(parameter_path.rebuild(), value, hide=True)

        return output_path.rebuild()
