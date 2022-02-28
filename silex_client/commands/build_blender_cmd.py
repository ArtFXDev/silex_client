from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    RadioSelectParameterMeta,
    TaskFileParameterMeta,
)
from silex_client.utils.tractor import dirmap

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BlenderCommand(CommandBase):
    """
    Construct Blender render commands
    See: https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(
                extensions=[".blend"], use_current_context=True
            ),
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
        "output_directory": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_extension": {"type": str, "hide": True, "value": "exr"},
        "engine": {
            "label": "Render engine",
            "type": RadioSelectParameterMeta(
                **{"Cycles": "CYCLES", "Evee": "BLENDER_EEVEE"}
            ),
        },
    }

    EXTENSIONS_MAPPING = {"exr": "OPEN_EXR", "png": "PNG", "jpg": "JPG", "tiff": "TIFF"}

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
        output_extension = self.EXTENSIONS_MAPPING[parameters["output_extension"]]

        # Build the Blender command
        blender_cmd = command_builder.CommandBuilder(
            "blender", rez_packages=["blender"], delimiter=" ", dashes="--"
        )
        blender_cmd.param("background")
        # Scene file
        blender_cmd.value(dirmap(scene.as_posix()))
        blender_cmd.param("render-format", output_extension)
        blender_cmd.param("engine", parameters["engine"])
        blender_cmd.param(
            "render-output",
            dirmap(
                (
                    parameters["output_directory"] / parameters["output_filename"]
                ).as_posix()
            ),
        )
        blender_cmd.param("log-level", 0)

        commands: Dict[str, command_builder.CommandBuilder] = {}

        # Split frames by task size
        frame_chunks = split_frameset(frame_range, task_size)

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = blender_cmd.deepcopy()

            fmt_frames = ",".join(map(str, list(chunk)))

            task_title = chunk.frameRange()

            # Add the frames argument
            commands[task_title] = chunk_cmd.param("render-frame", fmt_frames)

        return {"commands": {f"Scene: {scene.stem}": commands}, "file_name": scene.stem}
