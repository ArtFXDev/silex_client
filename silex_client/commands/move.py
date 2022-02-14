from __future__ import annotations

import logging
import os
import pathlib
import shutil
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils.enums import ConflictBehaviour
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
        src_paths: List[pathlib.Path] = parameters["src"]
        dst_path: pathlib.Path = parameters["dst"]
        force: bool = parameters["force"]

        os.makedirs(dst_path, exist_ok=True)

        src_sequences = fileseq.findSequencesInList(src_paths)
        logger.info("Moving %s to %s", src_sequences, dst_path)

        label = self.command_buffer.label
        progress = SharedVariable(0)

        async with UpdateProgress(
            self.command_buffer,
            action_query,
            progress,
            SharedVariable(len(src_paths)),
            0.2,
        ):
            for index, src_path in enumerate(src_paths):
                progress.value = index + 1
                self.command_buffer.label = f"{label} ({index+1}/{len(src_paths)})"

                # Check for file to copy
                if not os.path.exists(src_path):
                    raise Exception(f"{src_path} doesn't exist.")

                new_path = dst_path
                if new_path.is_dir():
                    new_path = new_path / src_path.name

                # Handle override of existing file
                if new_path.exists() and force:
                    await execute_in_thread(self.remove, new_path)
                elif new_path.exists():

                    conflict_behaviour = action_query.store.get(
                        "file_conflict_behaviour"
                    )
                    if conflict_behaviour is None:
                        conflict_behaviour = await prompt_override(
                            self, new_path, action_query
                        )
                    if conflict_behaviour in [
                        ConflictBehaviour.ALWAYS_OVERRIDE,
                        ConflictBehaviour.ALWAYS_KEEP_EXISTING,
                    ]:
                        action_query.store[
                            "file_conflict_behaviour"
                        ] = conflict_behaviour
                    if conflict_behaviour in [
                        ConflictBehaviour.OVERRIDE,
                        ConflictBehaviour.ALWAYS_OVERRIDE,
                    ]:
                        force = True
                        await execute_in_thread(self.remove, new_path)
                    if conflict_behaviour in [
                        ConflictBehaviour.KEEP_EXISTING,
                        ConflictBehaviour.ALWAYS_KEEP_EXISTING,
                    ]:
                        await execute_in_thread(self.remove, src_path)
                        continue

                logger.info(f"Moving file from {src_path} to {dst_path}")
                await execute_in_thread(self.move, str(src_path), str(dst_path))
