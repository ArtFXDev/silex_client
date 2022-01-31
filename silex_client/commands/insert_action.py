from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.command_buffer import CommandParameters
from silex_client.action.connection import Connection
from silex_client.utils.parameter_types import AnyParameter, StringParameterMeta
from silex_client.action.action_query import ActionQuery


class InsertAction(CommandBase):
    """
    Insert an action right into the current action as a child.

    The inserted action will be executed right after the current step, make sure
    this command is called at the end of a step if you want the inserted action to be
    executed right after being inserted.

    You can customise dynamically the inserted action using the append_step and prepend_step
    parameters.
    """

    parameters = {
        "name": {
            "label": "Name of the action to insert",
            "type": StringParameterMeta(),
            "value": "",
            "tooltip": """
            Name of the action to insert.
            If the definition is empty, this name will be used to find
            the definition in the config files
            """,
        },
        "category": {
            "label": "Action category",
            "type": StringParameterMeta(),
            "value": "action",
            "tooltip": """
            If the action to insert is an action name
            This define the category of the action to resolve
            """,
        },
        "definition": {
            "label": "Action definition",
            "type": dict,
            "value": {},
            "tooltip": """
            If you don't provide any action definition, the definition will be resolved
            from the available action config files
            """,
            "hide": True,
        },
        "prepend_step": {
            "label": "Action to prepend",
            "type": dict,
            "value": {},
            "tooltip": """
            You can provide a step definition to customize the inserted action
            dynamically
            The step will be preprended in the inserted action
            """,
            "hide": True,
        },
        "append_step": {
            "label": "Action to append",
            "type": dict,
            "value": {},
            "tooltip": """
            You can provide a step definition to customize the inserted action
            dynamically
            The step will be appended in the inserted action
            """,
            "hide": True,
        },
        "input": {
            "label": "Action input value",
            "type": AnyParameter,
            "value": {},
            "tooltip": "This value will be set to the newly inserted action's input",
            "hide": True,
        },
        "parameters_override": {
            "label": "Parameters to set on the action",
            "type": dict,
            "value": {},
            "tooltip": """
            Dict of values to set on the parameters of the inserted action
            The keys of the dict should look like <step>.<command>.<parameter>
            """,
            "hide": True,
        },
        "label": {
            "label": "Action label",
            "type": StringParameterMeta(),
            "value": "",
            "tooltip": "The label to append to the inserted action's label",
            "hide": True,
        },
        "index_shift": {
            "label": "Index margin",
            "type": int,
            "value": 10,
            "tooltip": """
            When inserting the action, the index will be set automatically so the
            action is set between the current steps and the next step.
            This is done by shifting the index of the following steps, you can choose,
            how big is the shift with this parameter.
            """,
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: CommandParameters,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        name: str = parameters["name"]
        category: str = parameters["category"]
        definition: dict = parameters["definition"]
        prepend_step: dict = parameters["prepend_step"]
        append_step: dict = parameters["append_step"]
        action_input: Any = parameters["input"]
        parameters_override: Dict[str, Any] = parameters["parameters_override"]
        label: str = parameters["label"]
        index_shift: int = parameters["index_shift"]

        main_action = ActionQuery(name=name, category=category, definition=definition)
        if not main_action:
            raise Exception(f"Could not resolve the action {name}")

        # The user can pass action definitions to prepend or append to the inserted action.
        # It can be used to customise the action dynamicaly
        for index, insert_step in enumerate([prepend_step, append_step]):
            if not insert_step:
                continue

            action_children = list(main_action.buffer.children.values())

            # The index of the inserted definition is different if we prepend of append
            insert_index = action_children[0].index - index_shift
            if index == 1:
                insert_index = action_children[-1].index + index_shift

            insert_step["index"] = insert_index
            # We always need to make sure the inserted definitions does not override
            # existing children, we use uuid as name to avoid that
            main_action.buffer.deserialize({"steps": {str(uuid.uuid4()): insert_step}})

        # The parameter values of the inserted action can be overriden
        for parameter_path, parameter_value in parameters_override.items():
            parameter_value = self.command_buffer.resolve_io(
                action_query, parameter_value
            )
            main_action.set_parameter(parameter_path, parameter_value)

        if label:
            action_label = main_action.buffer.label
            main_action.buffer.label = (
                f"{action_label} {label}" if action_label else label
            )
        if action_input:
            main_action.buffer.input = action_input

        action_definition = main_action.buffer.serialize()

        # To insert the action between the existing children
        # we must shift the index of all the children that follow the current step
        parent_action = self.command_buffer.get_parent("actions")
        parent_step = self.command_buffer.get_parent("steps")
        if parent_action is None or parent_step is None:
            raise Exception(
                "Could not append new action: The current command is invalid"
            )

        action_definition["index"] = parent_step.index + index_shift
        parent_action_steps = list(parent_action.children.values())
        parent_step_index = parent_action_steps.index(parent_step)
        next_steps = parent_action_steps[parent_step_index + 1 :]

        for next_step in next_steps:
            next_step.index += index_shift * 2

        logger.info("Inserting action: %s", name)
        # We always need to make sure the inserted definitions does not override
        # existing children, we use uuid as name to avoid that
        action_name = str(uuid.uuid4())
        parent_action.deserialize({"actions": {action_name: action_definition}})

        # This command foward the output of the inserted action.
        return Connection(action_name + Connection.SPLIT + "output")
