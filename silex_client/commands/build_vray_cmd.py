from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils.command import CommandBuilder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    PathParameterMeta,
    RadioSelectParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class VrayCommand(CommandBase):
    """
    Construct V-Ray render commands
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": PathParameterMeta(extensions=[".vrscene"]),
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
        "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "engine": {
            "label": "RT engine",
            "type": RadioSelectParameterMeta(
                **{"Regular": 0, "CPU RT": 1, "GPU CUDA": 5, "GPU RTX": 7}
            ),
            "value": 0,
        },
        "parameter_overrides": {
            "type": bool,
            "label": "Parameter overrides",
            "value": False,
        },
        "resolution": {
            "label": "Resolution ( width, height )",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
            "hide": True,
        },
    }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        hide_overrides = not parameters["parameter_overrides"]
        self.command_buffer.parameters["resolution"].hide = hide_overrides

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
        skip_existing = int(parameters["skip_existing"])
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int] = parameters["resolution"]

        # Build the V-Ray command
        vray_cmd = CommandBuilder("vray", rez_packages=["vray"])
        vray_cmd.disable(["display", "progressUseColor", "progressUseCR"])
        vray_cmd.param("progressIncrement", 5)
        vray_cmd.param("verboseLevel", 3)
        vray_cmd.param("rtEngine", parameters["engine"])
        vray_cmd.param("skipExistingFrames", skip_existing)
        vray_cmd.param("sceneFile", scene)
        vray_cmd.param("imgFile", parameters["output_filename"])

        # If the user is connected
        if "project" in action_query.context_metadata:
            # Add the project in the rez environment
            vray_cmd.add_rez_package(action_query.context_metadata["project"].lower())

        if parameter_overrides:
            vray_cmd.param("imgWidth", resolution[0]).param("imgHeight", resolution[1])

        commands: Dict[str, CommandBuilder] = {}

        # Split frames by task size
        frame_chunks = split_frameset(frame_range, task_size)

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = vray_cmd.deepcopy()

            fmt_frames = ";".join(map(str, list(chunk)))

            task_title = chunk.frameRange()

            # Add the frames argument
            commands[task_title] = chunk_cmd.param("frames", fmt_frames)

        return {"commands": commands, "file_name": scene.stem}
