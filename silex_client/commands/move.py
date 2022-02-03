from __future__ import annotations

import logging
import os
import pathlib
import shutil
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.prompt import prompt_override, UpdateProgress
from silex_client.utils.parameter_types import ListParameterMeta
from silex_client.utils.thread import execute_in_thread

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

    @staticmethod
    def remove(path: str):
        if os.path.isdir(path):
            # clean tree
            shutil.rmtree(path)

        if os.path.isfile(path):
            os.remove(path)

    @staticmethod
    def move(src: str, dst: str):

        os.makedirs(dst, exist_ok=True)

        # Move folder or file
        if os.path.isdir(src):
            # Move all file in dst folder
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

        label = self.command_buffer.label
        progress = SharedVariable(0)
        async with UpdateProgress(
            self.command_buffer,
            action_query,
            progress,
            SharedVariable(len(src)),
            0.2,
        ):
            for index, item in enumerate(src):
                progress.value = index + 1
                self.command_buffer.label = f"{label} ({index+1}/{len(src)})"

                # Check for file to copy
                if not os.path.exists(item):
                    raise Exception(f"{item} doesn't exist.")

                new_path = pathlib.Path(dst)
                destination_path = dst
                if not os.path.isdir(item):
                    destination_path = os.path.join(dst, os.path.basename(item))
                # Handle override of existing file
                if new_path.exists() and force:
                    await execute_in_thread(self.remove, destination_path)
                elif new_path.exists():
                    response = action_query.store.get("file_conflict_policy")
                    if response is None:
                        response = await prompt_override(self, new_path, action_query)
                    if response in ["Always override", "Always keep existing"]:
                        action_query.store["file_conflict_policy"] = response
                    if response in ["Override", "Always override"]:
                        force = True
                        await execute_in_thread(self.remove, destination_path)
                    if response in ["Keep existing", "Always keep existing"]:
                        await execute_in_thread(self.remove, item)
                        continue

                logger.info(f"Moving file from {item} to {dst}")
                await execute_in_thread(self.move, item, dst)

