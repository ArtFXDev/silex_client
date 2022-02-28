from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildNukeCommand(CommandBase):
    """
    Construct Nuke render commands
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".nk"], use_current_context=True),
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
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
        task_size: int = parameters["task_size"]

        nuke_cmd = command_builder.CommandBuilder(
            "nuke", rez_packages=["nuke"], delimiter=" "
        )
        nuke_cmd.param("-gpu").param("-multigpu")  # Use gpu
        nuke_cmd.param("-sro")  # Follow write order
        nuke_cmd.param("-priority", "high")

        frame_chunks = split_frameset(frame_range, task_size)
        commands: Dict[str, command_builder.CommandBuilder] = {}

        for chunk in frame_chunks:
            chunk_cmd = nuke_cmd.deepcopy()

            # Specify the frames
            chunk_cmd.param("F", chunk.frameRange())

            # Specify the scene file
            chunk_cmd.param("xi", str(scene))

            commands[chunk.frameRange()] = chunk_cmd

        return {
            "commands": {f"Script: {scene.stem}": commands},
            "file_name": scene.stem,
        }
