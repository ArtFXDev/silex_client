from __future__ import annotations

import os
import pathlib
import shutil
import logging
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import ConflictBehaviour
from silex_client.utils.prompt import UpdateProgress, prompt_override
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.datatypes import SharedVariable

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class Copy(CommandBase):
    """
    Copy files and override if asked
    """

    parameters = {
        "src": {
            "label": "Source path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Select the file or the directory you want to copy",
        },
        "dst": {
            "label": "Destination directory",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Select the directory in wich you want to copy you file(s)",
        },
        "force": {
            "label": "Force override existing files",
            "type": bool,
            "value": True,
            "tooltip": "If a file already exists, it will be overriden without prompt",
        },
    }

    @staticmethod
    def copy(src: pathlib.Path, dst: pathlib.Path, progress: SharedVariable):
        """
        The default shutil copy copies the files with very small chunks which end up
        with poor copy performances on windows. This is an equivalent of the copy with
        a bigger chunk size and progress information
        """
        with open(src, "rb") as fsrc:
            with open(dst, "wb") as fdst:
                while 1:
                    buf = fsrc.read(64 * 1024 * 1)
                    if not buf:
                        break
                    progress.value += fdst.write(buf)

        shutil.copymode(src, dst)
        return progress

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        src_paths: List[pathlib.Path] = parameters["src"]
        dst_paths: List[pathlib.Path] = parameters["dst"]
        force: bool = parameters["force"]

        src_sequences = fileseq.findSequencesInList(src_paths)
        dst_sequences = fileseq.findSequencesInList(dst_paths)
        logger.info("Copying %s to %s", src_sequences, dst_sequences)

        label = self.command_buffer.label
        total_file_size = SharedVariable(
            sum(os.path.getsize(path) for path in src_paths)
        )
        progress: SharedVariable = SharedVariable(0)

        async with UpdateProgress(
            self.command_buffer, action_query, progress, total_file_size, 0.2
        ):
            for index, src_path in enumerate(src_paths):
                self.command_buffer.label = f"{label} ({index+1}/{len(src_paths)})"

                dst_path = dst_paths[index % len(dst_paths)]

                if not src_path.exists():
                    raise Exception(f"Source path {src_path} does not exists")

                if dst_path.is_dir():
                    dst_path = dst_path / src_path.name
                    dst_paths[index] = dst_path

                # Handle override of existing file
                if dst_path.exists() and force:
                    await execute_in_thread(os.remove, dst_path)
                elif dst_path.exists():
                    conflict_behaviour = action_query.store.get(
                        "file_conflict_behaviour"
                    )
                    if conflict_behaviour is None:
                        conflict_behaviour = await prompt_override(
                            self, dst_path, action_query
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
                        await execute_in_thread(os.remove, dst_path)
                    if conflict_behaviour in [
                        ConflictBehaviour.KEEP_EXISTING,
                        ConflictBehaviour.ALWAYS_KEEP_EXISTING,
                    ]:
                        await execute_in_thread(os.remove, src_path)
                        continue

                os.makedirs(str(dst_path.parent), exist_ok=True)
                await execute_in_thread(self.copy, src_path, dst_path, progress)

        return {
            "source_paths": src_paths,
            "destination_dirs": [dst_path.parent for dst_path in dst_paths],
            "destination_paths": dst_paths,
        }
