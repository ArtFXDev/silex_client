from __future__ import annotations

import contextlib
import logging
import pathlib
import typing
from typing import Any, Dict

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import AnyParameter

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetStoredValue(CommandBase):
    """
    Store a given value into the action's global store
    """

    parameters = {
        "key": {
            "label": "Key",
            "type": str,
            "value": None,
            "hide": True,
        },
        "key_suffix": {
            "label": "Key suffix",
            "type": str,
            "value": None,
            "hide": True,
        },
        "value": {
            "label": "Value",
            "type": AnyParameter,
            "value": None,
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
        key: str = parameters["key"]
        key_suffix: str = parameters["key_suffix"]
        value: Any = parameters["value"]

        if key_suffix:
            key = f"{key}:{key_suffix}"

        action_query.store[key] = value
        return {"value": value, "key": key}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        key_suffix = self.command_buffer.parameters["key_suffix"].get_value(
            action_query
        )

        if key_suffix is None:
            return

        # Handle file_paths in key suffix
        with contextlib.suppress(OSError):
            if isinstance(key_suffix, list):
                sequences = fileseq.findSequencesInList(key_suffix)
                key_suffix = pathlib.Path(str(sequences[0].dirname()))
            elif pathlib.Path(str(key_suffix)).is_file():
                key_suffix = pathlib.Path(str(key_suffix)).parent

        self.command_buffer.parameters["key_suffix"].command_output = False
        self.command_buffer.parameters["key_suffix"].value = key_suffix
