from __future__ import annotations

import asyncio
import logging
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.datatypes import SharedVariable

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import pathlib
import shutil


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
    }

    @staticmethod
    def copy(src: pathlib.Path, dst: pathlib.Path, progress: SharedVariable):
        if dst.is_dir():
            dst = dst / src.name

        with open(src, "rb") as fsrc:
            with open(dst, "wb") as fdst:
                while 1:
                    buf = fsrc.read(64 * 1024 * 1)
                    if not buf:
                        break
                    progress.value += fdst.write(buf)

        shutil.copymode(src, dst)
        return progress

    async def update_progress(
        self,
        action_query: ActionQuery,
        progress: SharedVariable,
        total: int,
    ):
        while True:
            try:
                await asyncio.sleep(0.2)
                self.command_buffer.progress = int((progress.value / total) * 100)
                await action_query.async_update_websocket()
            except asyncio.CancelledError:
                self.command_buffer.progress = 100
                await action_query.async_update_websocket()
                break

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        source_paths: List[pathlib.Path] = parameters["src"]
        destination_dirs: List[pathlib.Path] = parameters["dst"]

        destination_paths = []

        source_sequences = fileseq.findSequencesInList(source_paths)
        destination_sequences = fileseq.findSequencesInList(destination_dirs)
        logger.info("Copying %s to %s", source_sequences, destination_sequences)

        # Loop over all the files to copy
        label = self.command_buffer.label
        total_file_size: int = sum(os.path.getsize(path) for path in source_paths)

        progress: SharedVariable = SharedVariable(0)
        progress_task = asyncio.create_task(
            self.update_progress(action_query, progress, total_file_size)
        )

        for index, source_path in enumerate(source_paths):
            self.command_buffer.label = f"{label} ({index+1}/{len(source_paths)})"
            # If only one directory is given, this will still work thanks to the modulo
            destination_dir = destination_dirs[index % len(destination_dirs)]
            # Check the file to copy
            if not source_path.exists():
                raise Exception(f"Source path {source_path} does not exists")

            # Copy only if the files does not already exists
            os.makedirs(str(destination_dir), exist_ok=True)
            await execute_in_thread(self.copy, source_path, destination_dir, progress)

            destination_paths.append(destination_dir / source_path.name)

        progress_task.cancel()

        return {
            "source_paths": source_paths,
            "destination_dirs": destination_dirs,
            "destination_paths": destination_paths,
        }
