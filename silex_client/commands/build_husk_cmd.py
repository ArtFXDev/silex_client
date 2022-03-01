from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    TaskFileParameterMeta,
)
from silex_client.utils.tractor import dirmap

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class HuskCommand(CommandBase):
    """
    Construct Husk render commands
    See: https://www.sidefx.com/docs/houdini/ref/utils/husk.html
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(
                extensions=[".usd", ".usda", ".usdc"], use_current_context=True
            ),
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": IntArrayParameterMeta(3),
            "value": [1, 50, 1],
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "output_directory": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_extension": {"type": str, "hide": True, "value": "exr"},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        frame_range: List[int] = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        full_path = f"{(parameters['output_directory'] / parameters['output_filename']).as_posix()}.$F4.{parameters['output_extension']}"

        husk_cmd = command_builder.CommandBuilder(
            "husk", rez_packages=["houdini"], delimiter=" ", dashes="--"
        )
        husk_cmd.param("usd-input", dirmap(scene.as_posix()))
        husk_cmd.param("output", dirmap(full_path))
        husk_cmd.param("make-output-path")
        husk_cmd.param("exrmode", 1)
        husk_cmd.param("verbose", "3a")

        commands: Dict[str, command_builder.CommandBuilder] = {}

        # Split frames by task size
        frame_chunks = split_frameset(
            FrameSet.from_range(frame_range[0], frame_range[1], frame_range[2]),
            task_size,
        )

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = husk_cmd.deepcopy()
            task_title = chunk.frameRange()

            start = int(chunk[0])
            end = int(chunk[-1])
            step = int(frame_range[2])

            chunk_cmd.param("frame", start)
            chunk_cmd.param("frame-count", end - start + 1)
            chunk_cmd.param("frame-inc", step)

            # Add the frames argument
            commands[task_title] = chunk_cmd

        logger.error(commands)

        return {"commands": {f"Scene: {scene.stem}": commands}, "file_name": scene.stem}
