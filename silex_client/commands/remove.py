from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List

from silex_client.action.command_base import CommandBase

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import pathlib
import shutil
from typing import List

from silex_client.utils.parameter_types import ListParameterMeta


class Remove(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": ListParameterMeta(pathlib.Path),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        file_path: List[pathlib.Path] = parameters["file_path"]

        for item in file_path:
            # Check for file to copy
            if not os.path.exists(item):
                raise Exception(f"{item} doesn't exist.")

            if os.path.isfile(item):
                os.remove(item)
            else:
                shutil.rmtree(item)

            logger.info(f"OK remove {item}")
