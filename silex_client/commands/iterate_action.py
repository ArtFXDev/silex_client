"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of the IterateAction command
"""
from __future__ import annotations

from collections.abc import Sized
import logging
import typing
from typing import Any, Dict, List

from silex_client.action.command_definition import CommandDefinition
from silex_client.action.command_sockets import CommandSockets
from silex_client.commands.insert_action import InsertAction
from silex_client.utils.socket_types import (
    ListType,
    StringType,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class IterateAction(InsertAction):
    """
    Same as the InsertAction command.
    All the parameters are now list of parameters, you can set a parameter with a
    list of one item to use this value for all the iterations
    """

    inputs = {
        "iterations": {
            "label": "Iteration count",
            "type": int,
            "value": 0,
        },
        "names": {
            "label": "Name of the actions to insert",
            "type": ListType(StringType()),
            "value": [""],
            "tooltip": """
            Name of the actions to insert.
            If the definition is empty, this name will be used to find
            the definition in the config files
            """,
        },
        "categories": {
            "label": "Action categories",
            "type": ListType(StringType()),
            "value": ["action"],
            "tooltip": """
            If the actions to insert are action name
            This define the category of the actions to resolve
            """,
        },
        "definitions": {
            "label": "Action definitions",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": """
            If you don't provide any action definitions, the definitions will be resolved
            from the available action config files
            """,
            "hide": True,
        },
        "prepend_steps": {
            "label": "Steps to prepend",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": """
            You can provide step definitions to customize the inserted action
            dynamically
            These steps will be preprended in the inserted actions
            """,
            "hide": True,
        },
        "append_steps": {
            "label": "Steps to append",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": """
            You can provide step definitions to customize the inserted action
            dynamically
            These steps will be appended in the inserted actions
            """,
            "hide": True,
        },
        "inputs": {
            "label": "Action inputs value",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": "These values will be set to the newly inserted action's input",
            "hide": True,
        },
        "inputs_overrides": {
            "label": "Inputs to set on the actions",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": """
            Dict of values to set on the inputs of the inserted action
            The keys of the dict should look like <step>.<command>.<input>
            """,
            "hide": True,
        },
        "labels": {
            "label": "Actions labels",
            "type": ListType(StringType()),
            "value": [""],
            "tooltip": "The labels to append to the inserted actions's label",
            "hide": True,
        },
    }

    outputs = {
        "actions_output": {
            "label": "Actions's output",
            "type": ListType(dict),
            "value": [{}],
            "tooltip": "The outputs of the actions can be retrieved here",
        }
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        iterations: int = parameters["iterations"]
        names: List[str] = parameters["names"]
        categories: List[str] = parameters["categories"]
        definitions: List[dict] = parameters["definitions"]
        prepend_steps: List[dict] = parameters["prepend_steps"]
        append_steps: List[dict] = parameters["append_steps"]
        action_inputs: List[dict] = parameters["inputs"]
        inputs_overrides: List[Dict[str, Any]] = parameters["inputs_overrides"]
        labels: List[str] = parameters["labels"]

        outputs = []

        logger.info("Inserting %s actions: %s", iterations, names)
        for iteration in range(iterations - 1, -1, -1):
            # Every parameters are the same as the insert action but as list
            # To allow users to not have to set multiple times the same values
            # we use the modulo of the iteration to get the index of the value
            name: str = names[iteration % len(names)]
            category: str = categories[iteration % len(categories)]
            definition: dict = definitions[iteration % len(definitions)]
            prepend_step: dict = prepend_steps[iteration % len(prepend_steps)]
            append_step: dict = append_steps[iteration % len(append_steps)]
            action_input: Any = action_inputs[iteration % len(action_inputs)]
            inputs_override: Dict[str, Any] = inputs_overrides[
                iteration % len(inputs_overrides)
            ]
            label: str = labels[iteration % len(labels)]

            # When inheriting from an other command, our parameters are merges
            # with the child command's parameters. We update our parameters with the
            # values at the current index
            parameters.update(
                {
                    "name": name,
                    "category": category,
                    "definition": definition,
                    "prepend_step": prepend_step,
                    "append_step": append_step,
                    "input": action_input,
                    "inputs_override": inputs_override,
                    "label": label,
                }
            )
            output = await super().__call__(parameters, action_query, logger)
            outputs.append(output)

        return {"actions_output": outputs}

    async def setup(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        await super().setup(parameters, action_query, logger)

        # The number of iteration can be a sized variable
        if isinstance(parameters.get_raw("iterations", 0), Sized):
            parameters["iterations"] = len(parameters["iterations"])

        # By inheriting from an other class we also get all its parameters.
        # We must hide them all since they will be overriden by the values in the lists parameters
        for key, _ in super().inputs.items():
            parameter = self.buffer.inputs.get(key)
            if parameter is not None:
                parameter.hide = True
