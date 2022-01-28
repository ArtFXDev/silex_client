from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils import frames
from silex_client.utils.command import CommandBuilder
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
        self, file_path: pathlib.Path, frame_range: fileseq.FrameSet, logger
    ) -> List[str]:
        """
        Return a file sequence for a specific frame range
        """

        without_extension: pathlib.Path = file_path.parents[0] / file_path.stem
        frame_pattern = f".{frame_range}#{file_path.suffix}"

        sequence = fileseq.FileSequence(
            without_extension.with_suffix(frame_pattern),
        )

        return list(sequence)

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Target a ass file in a sequence to be used as pattern
        ass_file: pathlib.Path = parameters["ass_file"]

        output_filename: pathlib.Path = parameters["output_filename"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]

        kick_cmd = (
            CommandBuilder("powershell.exe", delimiter=" ")
            .param("ExecutionPolicy", "Bypass")
            .param("NoProfile")
            .param("File", "\\\\prod.silex.artfx.fr\\rez\\windows\\render_kick_ass.ps1")
        )

        kick_cmd.param("ExportFile", str(output_filename))

        # Split frames by task
        frame_chunks = frames.split_frameset(frame_range, task_size)
        commands: Dict[str, CommandBuilder] = dict()

        # Create commands
        for chunk in frame_chunks:
            chunk_cmd = kick_cmd.deepcopy()

            # Get ass sequence  using a specific frame_range
            ass_files: List[str] = self._find_sequence(
                ass_file, fileseq.FrameSet(chunk), logger
            )

            # Converting chunk back to a frame set
            task_name = chunk.frameRange()

            chunk_cmd.param("AssFiles", ",".join(ass_files))

            # Add ass sequence to argument list
            commands[task_name] = chunk_cmd

        return {"commands": commands, "file_name": ass_file.stem}
