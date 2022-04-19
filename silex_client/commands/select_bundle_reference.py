from __future__ import annotations

import copy
import logging
import pathlib
import typing
import os
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.commands.select_conform import SelectConform
from silex_client.resolve.config import Config
from silex_client.utils.parameter_types import PathParameterMeta, SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectBundleReference(SelectConform):
    """
    Handles assignement of a new bundle type (references only) e and wait for its response
    """

    parameters = {
        "file_paths": {
            "label": "insert file to bundle",
            "type": PathParameterMeta(multiple=True),
            "hide": True
        },
        "find_sequence": {
            "label": "Bundle the sequence of the selected file",
            "type": bool,
            "value": False,
            "tooltip": "The file sequences will be automaticaly detected from the file you select",
        },
        "auto_select_type": {
            "label": "Auto select the conform type",
            "type": bool,
            "value": True,
            'hide': True,
            "tooltip": "Guess the conform type from the extension",
        },
        "conform_type": {
            "label": "Select a conform type",
            "type": SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config.get().conforms]
            ),
            "value": None,
            'hide': True,
            "tooltip": "Select a conform type in the list",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
       
        output =  await super().__call__(parameters, action_query, logger)

        for file in  output['files']:
            file.update({'is_reference': True})

        return output