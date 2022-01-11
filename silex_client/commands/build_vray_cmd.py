from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (IntArrayParameterMeta,
                                                PathParameterMeta)

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
        "resolution": {
            "label": "Resolution ( width, height )",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "export_dir": {
            "label": "File directory",
            "type": str,
            "value": "",
        },
        "exoprt_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": "",
        },
        "extension": {
            "label": "File extension",
            "type": str,
            "value": None,
            "hide": True,
        },
    }

    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        directory: str = parameters["export_dir"]
        exoprt_name: str = str(parameters["exoprt_name"])
        extension: str = parameters["extension"]
        scene: pathlib.Path = parameters["scene_file"]
        frame_range: FrameSet = parameters["frame_range"]
        resolution: List[int] = parameters["resolution"]
        task_size: int = parameters["task_size"]
        skip_existing: int = int(parameters["skip_existing"])

        arg_list = [
            # V-Ray exe path
            "C:/Maya2022/Maya2022/vray/bin/vray.exe",
            # Don't show VFB (render view)
            "-display=0",
            # Update frequency for logs
            "-progressUpdateFreq=2000",
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

        # Check if context
        if action_query.context_metadata.get("user_email") is not None:
            export_file = os.path.join(directory, f"{exoprt_name}.{extension}")
            arg_list.append(f"-imgFile={export_file}")
            arg_list.extend(
                [f"-imgWidth={resolution[0]}", f"-imgHeight={resolution[1]}"]
            )

        if frame_range is None:
            raise Exception("No frame range found")

        frame_chunks: List[str] = list(FrameSet(frame_range))

        # Cut frames by task
        task_chunks: List[Any] = list(self._chunks(frame_chunks, task_size))
        cmd_dict: Dict[str, str] = dict()

        # create commands
        for chunk in task_chunks:
            start, end = chunk[0], chunk[-1]
            frames: str = ";".join(map(str, chunk))
            logger.info(f"Creating a new task with frames: {start} to {end}")
            cmd_dict[f"frames={start}-{end}"] = arg_list + [f'-frames="{frames}"']

        return {"commands": cmd_dict, "file_name": scene.stem}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        # show resolution only if context
        if action_query.context_metadata.get("user_email") is None:
            self.command_buffer.parameters["resolution"].hide = True
