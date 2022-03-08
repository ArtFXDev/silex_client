from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.utils.prompt import prompt_override
from silex_client.utils.enums import ConflictBehaviour

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class CheckExisting(CommandBase):
    """
    Execute the given python code
    """

    parameters = {
        "file_paths": {
            "label": "File path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
        },
        "prompt_override": {
            "label": "Prompt if the file exists",
            "type": bool,
            "value": False,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_paths"]
        prompt: bool = parameters["prompt_override"]

        exists_all = all(file_path.exists() for file_path in file_paths)
        exists_any = any(file_path.exists() for file_path in file_paths)

        output = {
            "exists_all": exists_all,
            "exists_any": exists_any,
            "keep_existing": False,
            "override": True,
        }

        if prompt and exists_any:
            conflict_behaviour = action_query.store.get("file_conflict_behaviour")
            if conflict_behaviour is None:
                conflict_behaviour = await prompt_override(
                    self, file_paths, action_query
                )
            if conflict_behaviour in [
                ConflictBehaviour.ALWAYS_OVERRIDE,
                ConflictBehaviour.ALWAYS_KEEP_EXISTING,
            ]:
                action_query.store["file_conflict_behaviour"] = conflict_behaviour
            if conflict_behaviour in [
                ConflictBehaviour.OVERRIDE,
                ConflictBehaviour.ALWAYS_OVERRIDE,
            ]:
                output["override"] = True
                output["keep_existing"] = False
            if conflict_behaviour in [
                ConflictBehaviour.KEEP_EXISTING,
                ConflictBehaviour.ALWAYS_KEEP_EXISTING,
            ]:
                output["override"] = False
                output["keep_existing"] = True

        return output
