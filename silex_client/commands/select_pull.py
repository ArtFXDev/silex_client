from __future__ import annotations

import logging
import os
import pathlib
import re
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.commands.build_work_path import BuildWorkPath
from silex_client.core.context import Context
from silex_client.utils.parameter_types import TaskFileParameterMeta, TextParameterMeta
from silex_client.utils.files import expand_path

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectPull(BuildWorkPath):
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
        "prompt": {
            "label": "Prompt if publish exists",
            "type": bool,
            "value": False,
            "hide": True,
        },
        "mode": {
            "label": "File template mode",
            "type": str,
            "value": "output",
            "hide": True,
        },
    }

    required_metadata = ["project_file_tree"]

    def skip_next_command(self, action_query):
        action_query.commands[action_query.current_command_index + 1].skip = True

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        publish: pathlib.Path = parameters["publish"]
        prompt: bool = parameters["prompt"]
        mode: str = parameters["mode"]
        mode_templates = Context.get()["project_file_tree"].get(mode)

        work_path = pathlib.Path(
            await super().__call__(parameters, action_query, logger)
        )

        publishes = [publish]
        if not publish.is_dir():
            publish = publish.parent
        else:
            publishes = list(publish.iterdir())

        if all(file.exists() for file in publishes) and publishes and prompt:
            response = await self.prompt_user(
                action_query,
                {
                    "pull_info": ParameterBuffer(
                        name="pull_info",
                        label="Pull Info",
                        type=TextParameterMeta(color="info"),
                        value=f"A publish at {publish} already exists",
                    ),
                    "pull_bool": ParameterBuffer(
                        name="pull_info",
                        label="Do you want to backup the current version in your work folder ?",
                        type=bool,
                        value=False,
                    ),
                },
            )
            if not response["pull_bool"]:
                self.skip_next_command(action_query)
                return
        elif prompt:
            self.skip_next_command(action_query)
            return

        if mode_templates is None:
            raise Exception(
                "The given mode does not exists in the current project file tree"
            )

        expanded_path = expand_path(publish)
        pull_path = (
            work_path.parent
            / "publish_backup"
            / expanded_path.get("OutputType", "unknown")
        )
        os.makedirs(pull_path, exist_ok=True)
        versions = [
            child.name
            for child in pull_path.iterdir()
            if re.match(r"^v\d+$", child.name)
        ]
        versions.sort()
        version = "v001"
        if versions:
            version = "v" + str(int(versions[-1].lstrip("v")) + 1).zfill(3)

        return {"pull_dst": pull_path / version, "pull_src": publishes}
