from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.core.context import Context
from silex_client.utils.parameter_types import TaskFileParameterMeta
from silex_client.utils.files import expand_path

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectPull(CommandBase):
    """
    Select the file to pull into the current work directory
    """

    parameters = {
        "publish": {
            "label": "Select a publish",
            "type": TaskFileParameterMeta(),
            "value": None,
            "tooltip": "Select a submiter in the list",
        },
        "mode": {
            "label": "Path mode",
            "type": str,
            "value": "output",
        },
    }

    required_metadata = ["project_file_tree"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        publish: pathlib.Path = parameters["publish"]
        mode: str = parameters["mode"]
        mode_templates = Context.get()["project_file_tree"].get(mode)

        if mode_templates is None:
            raise Exception(
                "The given mode does not exists in the current project file tree"
            )

        if not publish.is_dir():
            publish = publish.parent
