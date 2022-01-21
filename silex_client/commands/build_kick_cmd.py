from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils import frames
from silex_client.utils.parameter_types import PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class KickCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "ass_file": {
            "label": "Select ass file",
            "type": PathParameterMeta(extensions=[".ass", ".ass.gz"]),
            "value": None,
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "output_filename": {"type": pathlib.Path, "value": "", "hide": True},
    }

    def _find_sequence(
        self, file_path: pathlib.Path, frame_range: fileseq.FrameSet
    ) -> List[pathlib.Path]:
        """
        Return a files sequence for a specific frame range
        """

        path_without_extenstion: pathlib.Path = file_path.parents[0] / file_path.stem
        extension: str = f".{frame_range}#.{file_path.suffix}"
        return list(
            fileseq.FileSequence(
                path_without_extenstion.with_suffix(extension),
                pad_style=fileseq.PAD_STYLE_HASH4,
            )
        )

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        ass_file: pathlib.Path = parameters[
            "ass_file"
        ]  # Target a ass file in a sequence to be used as pattern

        output_filename: pathlib.Path = parameters["output_filename"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]

        kick_list: List[str] = [
            "powershell.exe",
            "-ExecutionPolicy",
            "Bypass",
            "-NoProfile",
            "-File",
            "\\\\prod.silex.artfx.fr\\rez\\windows\\render_kick_ass.ps1",
            "-ExportFile",
            str(output_filename),
        ]

        # Create list of arguents
        if action_query.context_metadata["project"] is not None:

            # Prepend rez arguments
            rez_args: List[str] = [
                "rez",
                "env",
                action_query.context_metadata["project"].lower(),
                "--",
            ]

            kick_list = rez_args + kick_list

        # Check if frame_range exists
        if frame_range is None:
            raise Exception("No frame range found")

        # Cut frames by task
        frame_chunks: List[str] = list(fileseq.FrameSet(frame_range))
        task_chunks: List[List[str]] = list(frames.chunks(frame_chunks, task_size))
        commands: Dict[str, List[str]] = dict()

        # Create commands
        for chunk in task_chunks:
            # Get ass sequence  using a specific frame_range
            ass_files: List[pathlib.Path] = self._find_sequence(
                ass_file, fileseq.FrameSet(chunk)
            )

            # Converting chunk back to a frame set
            task_name = fileseq.FrameSet(chunk).frameRange()

            # Add ass sequence to argument list
            commands[task_name] = kick_list + [
                "-AssFiles",
                ",".join(map(str, ass_files)),
            ]

        return {"commands": commands, "file_name": ass_file.stem}
