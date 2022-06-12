from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class NukeRenderTasksCommand(CommandBase):
    """
    Construct Nuke render commands
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".nk"]),
        },
        "frame_range": {
            "label": "Frame range",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "enable_gpu": {
            "label": "Enable GPU",
            "type": bool,
            "value": True,
        },
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
        },
        "write_node": {
            "label": "Write node",
            "tooltip": "Name of the write node to execute",
            "type": str,
        },
        "use_selection": {
            "label": "Fill selected write node",
            "tooltip": "This feature works only if you launched this submit from nuke",
            "type": bool,
            "value": False,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        frame_range: FrameSet = parameters["frame_range"]
        enable_gpu: bool = parameters["enable_gpu"]
        task_size: int = parameters["task_size"]
        write_node: str = parameters["write_node"]

        nuke_cmd = command_builder.CommandBuilder(
            "nuke",
            rez_packages=["nuke", action_query.context_metadata["project"].lower()],
            delimiter=" ",
        )

        if enable_gpu:
            nuke_cmd.param("-gpu").param("-multigpu")  # Use gpu

        nuke_cmd.param("-sro")  # Follow write order
        nuke_cmd.param("-priority", "high")
        nuke_cmd.param("X", write_node)  # Specify the write node

        frame_chunks = split_frameset(frame_range, task_size)
        tasks: List[farm.Task] = []

        for chunk in frame_chunks:
            chunk_cmd = nuke_cmd.deepcopy()

            # Specify the frames
            chunk_cmd.param("F", str(chunk))

            # Specify the scene file
            chunk_cmd.param("xi", scene.as_posix())

            task = farm.Task(title=str(chunk))
            task.addCommand(
                farm.wrap_with_mount(
                    chunk_cmd, action_query.context_metadata.get("project_nas")
                )
            )

            tasks.append(task)

        return {
            "tasks": tasks,
            "file_name": scene.stem,
        }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        try:
            import nuke
        except ImportError:
            return

        use_selection_parameter = self.command_buffer.parameters["use_selection"]
        if use_selection_parameter.get_value(action_query):
            write_node_parameter = self.command_buffer.parameters["write_node"]
            for node in nuke.selectedNodes():
                if node.Class() == "Write":
                    write_node_parameter.value = node.name()
                    break

            use_selection_parameter.value = False
