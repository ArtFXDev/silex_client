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


class SelectBundle(SelectConform):
    """
    Helper to prompt the user for a new bundle type and wait for its response
    """

    parameters = {
        "file_paths": {
            "label": "insert file to bundle",
            "type": PathParameterMeta(multiple=True),
        },
        "export_directory": {
            "label" : 'Select an directory',
            "type": pathlib.Path,
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

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        if parameters['file_paths'] and parameters['export_directory'] is None:
            self.command_buffer.parameters['export_directory'].value = pathlib.Path(parameters["file_paths"][0]).parents[0] 

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_paths"]
        find_sequence: bool = parameters["find_sequence"]
        export_directory: pathlib.Path = parameters["export_directory"]


        # Reset environment variable if it already exists 
        if "BUNDLE_ROOT" in os.environ : 
            del os.environ["BUNDLE_ROOT"]
        os.environ["BUNDLE_ROOT"] = str(export_directory / f'BUNDLE_{file_paths[0].stem}')


        os.makedirs(os.environ.get("BUNDLE_ROOT"), exist_ok=True)

        return await super().__call__(parameters, action_query, logger)
  
      