from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm, frames
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class KickRenderTasksCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "ass_folders": {
            "label": "Select Ass folders (render layers)",
            "type": TaskFileParameterMeta(
                extensions=[".ass"], directory=True, multiple=True
            ),
        },
        "frame_range": {
            "label": "Frame range",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True,
        },
        "output_path": {"type": pathlib.Path, "value": "", "hide": True},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        ass_folders: List[pathlib.Path] = parameters["ass_folders"]
        output_path: pathlib.Path = parameters["output_path"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        skip_existing = int(parameters["skip_existing"])

        tasks: List[farm.Task] = []

        ass_files = [
            f for f in os.listdir(ass_folders[0]) if pathlib.Path(f).suffix == ".ass"
        ]

        for ass_folder in ass_folders:
            output_path_layer = (
                output_path.parent
                / ass_folder.stem
                / f"{output_path.stem}_{ass_folder.stem}{''.join(output_path.suffixes)}"
            )

            kick_cmd = (
                command_builder.CommandBuilder(
                    "python",
                    rez_packages=[
                        "krender",
                        action_query.context_metadata["project"].lower(),
                    ],
                )
                .param("m")
                .value("krender")
                .param("assFolder", ass_folder.as_posix())
                .param("imgFile", output_path_layer.as_posix())
                .param("skipExistingFrames", skip_existing)
            )

            folder_task = farm.Task(title=ass_folder.stem)
            frame_chunks = frames.split_frameset(frame_range, task_size)

            for chunk in frame_chunks:
                chunk_cmd = kick_cmd.deepcopy()

                chunk_cmd.param("frames", chunk.frameRange())
                task = farm.Task(title=chunk.frameRange(), argv=chunk_cmd.as_argv())
                task.add_mount_command(action_query.context_metadata["project_nas"])

                if len(ass_folders) > 1:
                    folder_task.addChild(task)
                else:
                    tasks.append(task)

            if len(ass_folders) > 1:
                tasks.append(folder_task)

        return {"tasks": tasks, "file_name": ass_files[0]}
