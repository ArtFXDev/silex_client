from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
import logging

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.parameter_types import ListParameter
import shutil
import os
import pathlib


class Remove(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": ListParameter,
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

        file_path: pathlib.Path = parameters.get("file_path")

        for item in file_path:
            # Check for file to copy
            if not os.path.exists(item):
                raise Exception(f"{item} doesn't exist.")

            if os.path.isfile(item):
                os.remove(item)
            else:
                shutil.rmtree(item)

            logger.info(f"OK remove {item}")
