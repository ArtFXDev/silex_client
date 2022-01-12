from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

import fileseq
from silex_maya.utils.utils import Utils

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta, PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import pathlib

import maya.cmds as cmds


class KickCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "ass_target": {
            "label": "Select ass file",
            "type": PathParameterMeta(extensions=[".ass", ".ass.gz"]),
            "value": None,
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "resolution": {
            "label": "Resolution ( width, height )",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "directory": {
            "label": "File directory",
            "type": str,
            "value": "",
        },
        "export_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": "",
        },
        "extension": {
            "label": "File extension",
            "type": str,
            "value": None,
            "hide": True,
        },
    }

    def _chunks(self, lst: List[Any], n: int) -> List[Any]:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def find_ass_sequence(self, directory: str, export_name: str, frame_list) -> List[str]:
        """
        return a list of ass files for a specific frame list
        """

        ass_files = list()

        for frame in frame_list:
            frame = str(frame)

            # Format frame number to 4 digits
            for i in range(4 - len(frame)):
                frame = "0" + frame

            # add new ass file to list
            ass_files.append(f"{os.path.join(directory, export_name)}.{frame}.ass")

        return ass_files

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        ass_target: pathlib.Path = parameters[
            "ass_target"
        ]  # target a ass in a sequence to use as pattern

        directory: str = parameters["directory"]
        export_name: str = parameters["export_name"]
        extension:  str = parameters["extension"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        reslution: List[int] = parameters["resolution"]
        task_size: int = parameters["task_size"]
        export_file: str = "NONE"

        # Create list of arguents
        if action_query.context_metadata.get("user_email") is not None:
            export_file = os.path.join(directory, f"{export_name}.{extension}")

        arg_list: List[Any] = [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-NoProfile",
            "-File",
            "\\\\prod.silex.artfx.fr\\rez\windows\\render_kick_ass.ps1",
            "-ResolutionX",
            str(reslution[0]),
            "-ResolutionY",
            str(reslution[1]),
            "-ExportFile",
            export_file,
        ]

        # check if frame_range exists
        if frame_range is None:
            raise Exception("No frame range found")

        # Cut frames by task
        frame_chunks: List[str] = list(FrameSet(frame_range))
        task_chunks: List[Any] = list(self._chunks(frame_chunks, task_size))
        cmd_dict: Dict[str, str] = dict()

        # create commands
        for chunk in task_chunks:
            start: int = chunk[0]
            end: int = chunk[-1]
            ass_dir: str = ass_target.parents[0]
            ass_name: str = ass_target.stem.split(".")[0]
            ass_files: str = self.find_ass_sequence(ass_dir, ass_name, chunk)
            logger.info(f"Creating a new task with frames: {start} to {end}")

            cmd_dict[f"frames={start}-{end}"] = arg_list + ['-AssFiles'] + [','.join(ass_files)]

        return {"commands": cmd_dict, "file_name": export_name}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # show resolution only if context
        if action_query.context_metadata.get("user_email") is None:
            self.command_buffer.parameters["resolution"].hide = True
