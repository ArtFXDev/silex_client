from __future__ import annotations

import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class VrayCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": pathlib.Path
        },
        "frame_range": {
            "label": "Frame range",
            "type": IntArrayParameterMeta(2),
            "value": [0, 100]
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True
        }
    }

    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        scene: pathlib.Path = parameters.get('scene_file')
        frame_range: List[int] = parameters.get("frame_range")
        task_size: int = parameters.get("task_size")
        skip_existing: int =  int(parameters.get("skip_existing"))

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

            # Render already existing frames or not
            f"-skipExistingFrames={skip_existing}",

            # Specify the scene file
            f"-sceneFile={scene}",

            # "-rtEngine=5", # CUDA or CPU?
            # f"-imgFile={scene.parents[0] / 'render' / scene.stem}.png"
        ]

        chunks = list(self._chunks(
            range(frame_range[0], frame_range[1] + 1), task_size))
        cmd_dict = dict()


        for chunk in chunks:
            start, end = chunk[0], chunk[-1]
            logger.info(f"Creating a new task with frames: {start} {end}")
            cmd_dict[f"frames={start}-{end}"] = arg_list + \
                [f"-frames={start}-{end}"]

        return {
            "commands": cmd_dict,
            "file_name": scene.stem
        }
