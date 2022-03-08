from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CheckExisting(CommandBase):
    """
    Execute the given python code
    """

    parameters = {
        "file_path": {
            "label": "File path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
        },
        "prompt_override": {
            "label": "Prompt if the file exists",
            "type": bool,
            "value": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_path"]
        prompt_override: bool = parameters["prompt_override"]

        exists_all = all(file_path.exists() for file_path in file_paths)
        exists_any = any(file_path.exists() for file_path in file_paths)

        return {"exists_all": exists_all, "exists_any": exists_any}
