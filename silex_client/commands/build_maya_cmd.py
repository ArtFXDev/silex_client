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
    SelectParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class MayaCommand(CommandBase):
    """
    Construct Maya render commands
    """

    parameters = {
        "renderer": {
            "label": "Renderer",
            "type": SelectParameterMeta("vray", "arnold"),
            "value": "vray",
        },
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(
                extensions=[".ma", ".mb"], use_current_context=True
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
        # "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "output_folder": {"type": pathlib.Path, "hide": True, "value": ""},
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

        # Build the Blender command
        maya_cmd = command_builder.CommandBuilder(
            "Render", rez_packages=["maya"], delimiter=" ", dashes="-"
        )
        maya_cmd.param("r", parameters["renderer"])
        # Doesn't work need to check on a forum
        # maya_cmd.param("skipExistingFrames", str(parameters["skip_existing"]).lower())
        maya_cmd.param("rd", parameters["output_folder"])
        maya_cmd.param("im", parameters["output_filename"])
        maya_cmd.param("of", parameters["output_extension"])

        if parameters["renderer"] == "arnold":
            maya_cmd.param("ai:lve", 2)  # log level
            maya_cmd.param("fnc", 3)  # File naming name.#.ext

        commands: Dict[str, command_builder.CommandBuilder] = {}

        # Split frames by task size
        frame_chunks = split_frameset(
            FrameSet.from_range(frame_range[0], frame_range[1], frame_range[2]),
            task_size,
        )

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = maya_cmd.deepcopy()
            task_title = chunk.frameRange()

            chunk_cmd.param("s", chunk[0])
            chunk_cmd.param("e", chunk[-1])
            chunk_cmd.param("b", frame_range[2])

            # Add the scene file
            chunk_cmd.value(scene)

            # Add the frames argument
            commands[task_title] = chunk_cmd
            logger.error(str(chunk_cmd))

        return {"commands": {f"Scene: {scene.stem}": commands}, "file_name": scene.stem}
