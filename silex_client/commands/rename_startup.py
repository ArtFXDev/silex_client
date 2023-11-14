
from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
# from silex_houdini.utils.utils import Utils
from silex_client.utils.parameter_types import ListParameter
from silex_client.utils.log import flog


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os

import maya.cmds as cmds

class RenameStartup(CommandBase):
    """
    Save current scene with context as path
    """
    parameters = {
            "name": {
            "label": "Only set the path",
            "type": str,
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
        parent_path = pathlib.Path(parameters["name"]).parents[0]
        if not parent_path.exists():
            parent_path.mkdir(parents=True, exist_ok=True)
        cmds.file(rename= parameters["name"])

