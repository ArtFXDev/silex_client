from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List
import os
import pathlib
import shutil

from silex_client.action.command_base import CommandBase
from silex_client.utils.thread import execute_in_thread
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    TextParameterMeta,
    RadioSelectParameterMeta,
)

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Move(CommandBase):
    """
    Copy file and override if necessary
    """

    parameters = {
        "src": {
            "label": "File path",
            "type": ListParameterMeta(pathlib.Path),
            "value": None,
        },
        "dst": {
            "label": "Destination directory",
            "type": pathlib.Path,
            "value": None,
        },
        "force": {
            "label": "Force override existing files",
            "type": bool,
            "value": True,
            "tooltip": "If a file already exists, it will be overriden without prompt",
        },
    }

    async def _prompt_override(
        self, file_path: pathlib.Path, action_query: ActionQuery
    ) -> str:
        """
        Helper to prompt the user for a new conform type and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=f"The path:\n{file_path}\nAlready exists",
        )
        new_parameter = ParameterBuffer(
            type=RadioSelectParameterMeta(
                "Override", "Keep existing", "Always override", "Always keep existing"
            ),
            name="existing_file",
            label="Existing file",
        )
        # Prompt the user to get the new path
        response = await self.prompt_user(
            action_query,
            {
                "info": info_parameter,
                "existing_file": new_parameter,
            },
        )
        return response["existing_file"]

    @staticmethod
    def remove(path: str):
        if os.path.isdir(path):
            # clean tree
            shutil.rmtree(path)
            os.makedirs(path)

        if os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def move(src: str, dst: str):
        # move folder or file
        if os.path.isdir(src):
            # move all file in dst folder
            file_names = os.listdir(src)
            for file_name in file_names:
                shutil.move(os.path.join(src, file_name), dst)
        else:
            shutil.move(src, dst)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        src: List[str] = [str(source) for source in parameters["src"]]
        dst: str = str(parameters["dst"])
        force: bool = parameters["force"]

        # Check for file to copy
        if not os.path.exists(dst):
            raise Exception(f"{dst} doesn't exist.")

        for item in src:
            # Check for file to copy
            if not os.path.exists(item):
                raise Exception(f"{item} doesn't exist.")

            new_path = pathlib.Path(dst)
            destination_path = os.path.join(dst, os.path.basename(dst))
            # Handle override of existing file
            if new_path.exists() and force:
                await execute_in_thread(self.remove, destination_path)
            elif new_path.exists():
                response = action_query.store.get("move_override")
                if response is None:
                    response = await self._prompt_override(new_path, action_query)
                if response in ["Always override", "Always keep existing"]:
                    action_query.store["move_override"] = response
                if response in ["Override", "Always override"]:
                    force = True
                    await execute_in_thread(self.remove, destination_path)
                if response in ["Keep existing", "Always keep existing"]:
                    await execute_in_thread(self.remove, item)
                    continue

            logger.info(f"Moving file from {src} to {dst}")
            await execute_in_thread(self.move, item, dst)
