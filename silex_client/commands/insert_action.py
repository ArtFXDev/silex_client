from __future__ import annotations

import copy
import logging
import typing
import uuid
from typing import Any, Dict, Union

import fileseq
from tractor.api.author.base import StringListAttribute

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.parameter_types import AnyParameter, StringParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class InsertAction(CommandBase):
    """
    Insert an action's steps after the current step
    """

    #: When inserting an action, step, command... A margin between the indexes will be set
    AUTO_INDEX_MARGIN = 10

    parameters = {
        "name": {
            "label": "Name of the action to insert",
            "type": StringParameterMeta(),
            "value": None,
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
        "prepend": {
            "label": "Action to prepend",
            "type": dict,
            "value": {},
            "tooltip": """
            Similar to the definition parameter.
            The steps of this actions will be preprended in the inserted action
            """,
            "hide": True,
        },
        "append": {
            "label": "Action to append",
            "type": dict,
            "value": {},
            "tooltip": """
            Similar to the action parameter.
            The steps of this actions will be appended in the inserted action
            """,
            "hide": True,
        },
        "input": {
            "label": "Action input value",
            "type": AnyParameter,
            "value": "",
            "tooltip": "This value will be set to the newly inserted action's input",
            "hide": True,
        },
        "parameters": {
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
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        name: str = parameters["definition"]
        category: str = parameters["category"]
        definition: dict = parameters["definition"]
        prepend: dict = parameters["prepend"]
        append: dict = parameters["append"]
        action_input: Any = parameters["input"]
        parameter_values: Dict[str, Any] = parameters["parameter"]
        label: str = parameters["label"]

        main_action = ActionQuery(name=name, category=category, definition=definition)
        if not main_action:
            raise Exception(f"Could not resolve the action {name}")

        # The user can pass action definitions to prepend or append to the inserted action.
        # It can be used to customise the action dynamicaly
        for index, insert_definition in enumerate([prepend, append]):
            if not insert_definition:
                continue

            action_children = list(main_action.buffer.children.values())

            # The index of the inserted definition is different if we prepend of append
            insert_index = action_children[0].index - self.AUTO_INDEX_MARGIN
            if index == 1:
                insert_index = action_children[-1].index + self.AUTO_INDEX_MARGIN

            insert_definition["index"] = insert_index
            # We always need to make sure the inserted definitions does not override
            # existing children, we use uuid as name to avoid that
            insert_definition = {str(uuid.uuid4()): insert_definition}
            main_action.buffer.deserialize({"children": insert_definition})

        action_definition = main_action.buffer.serialize()

        # If the name action is inserted multiple times we need to make sure
        # this won't override existing actions
        unique_name = f"{name}_{uuid.uuid4()}"

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
