from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.utils.utils import chunks

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class VrayCommand(CommandBase):
    """
    build vray command
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
        skip_existing: int = int(parameters["skip_existing"])

        vray_args: List[str] = [
            # V-Ray exe path
            "C:/Maya2022/Maya2022/vray/bin/vray.exe",
            # Don't show VFB (render view)
            "-display=0",
            # Update frequency for logs
            "-progressIncrement=5",
            # Don't format logs with colors
            "-progressUseColor=0",
            # Use proper carrier returns
            "-progressUseCR=0",
            # Specify the scene file
            f"-sceneFile={scene}",
            # Render already existing frames or not
            f"-skipExistingFrames={skip_existing}",
            # "-rtEngine=5", # CUDA or CPU?
        ]

        # Check if project in context
        if "project" in action_query.context_metadata:
            # Prepend rez arguments
            rez_args: List[str] = [
                "rez",
                "env",
                action_query.context_metadata["project"].lower(),
                "--",
            ]

            vray_args = rez_args + vray_args

            # Add the V-Ray output path argument
            vray_args.append(f"-imgFile={parameters['output_filename']}")

        if frame_range is None:
            raise Exception("No frame range found")

        # Evaluate frame set expression
        frames_list: List[int] = list(FrameSet(frame_range))

        # Split frames by task size
        frame_chunks = list(chunks(frames_list, task_size))
        cmd_dict: Dict[str, List[str]] = dict()

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            fmt_frames = ";".join(map(str, chunk))

            # Converting the chunk back to a frame set
            task_title = FrameSet(chunk).frameRange()

            # Add the frames argument
            cmd_dict[task_title] = vray_args + ["-frames=", fmt_frames]

        return {"commands": cmd_dict, "file_name": scene.stem}
