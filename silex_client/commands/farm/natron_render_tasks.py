from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm, frames
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class NatronRenderTasksCommand(CommandBase):
    """
    Construct Natron render commands
    See: https://natron.readthedocs.io/en/rb-2.5/devel/natronexecution.html
    """

    parameters = {
        "scene_file": {
            "label": "Project file",
            "type": TaskFileParameterMeta(extensions=[".ntp"]),
        },
        "output_directory": {"type": pathlib.Path, "hide": True},
        "output_filename": {"type": str, "hide": True},
        "output_extension": {"type": str, "hide": True},
        "frame_range": {
            "label": "Frame range",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
        },
        "write_node": {"type": str, "value": "Write1"},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        output_directory: pathlib.Path = parameters["output_directory"]
        output_filename: str = parameters["output_filename"]
        output_extension: str = parameters["output_extension"]

        scene_file: pathlib.Path = parameters["scene_file"]
        write_node: str = parameters["write_node"]
        frame_range: FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]

        output_path = (
            output_directory
            / write_node
            / f"{output_filename}_{write_node}.####.{output_extension}"
        )

        natron_cmd = command_builder.CommandBuilder(
            "natronrenderer", rez_packages=["natron"], delimiter=None
        )

        tasks: List[farm.Task] = []
        frame_chunks = frames.split_frameset(frame_range, task_size)

        for chunk in frame_chunks:
            # Copy the initial command
            chunk_cmd = natron_cmd.deepcopy()

            chunk_range = str(chunk).replace("x", ":")
            chunk_cmd.param("w", [write_node, output_path, chunk_range])
            chunk_cmd.value(scene_file.as_posix())

            command = farm.wrap_with_mount(
                chunk_cmd, action_query.context_metadata.get("project_nas")
            )

            task = farm.Task(str(chunk))
            task.addCommand(command)
            tasks.append(task)

        return {"tasks": tasks, "file_name": scene_file.stem}
