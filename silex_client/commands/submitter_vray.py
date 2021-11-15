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

import tractor.api.author as author


class SubmitterVray(CommandBase):
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
        "frame_padding": {
            "label": "Frame split",
            "type": int,
            "value": 10
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        author.setEngineClientParam(debug=True)

        scene: pathlib.Path = parameters.get('scene_file')
        frame_range: list[int] =  parameters.get("frame_range")
        frame_padding: int = parameters.get("frame_padding")
        
        job = author.Job(title=f"vray render {scene.stem}")

        arg_list = [
            "C:/Maya2022/Maya2022/vray/bin/vray.exe",
            "-display=0",
            "-progressUpdateFreq=2000",
            "-progressUseColor=0",
            "-progressUseCR=0",
            f"-sceneFile={scene}",
            "-rtEngine=5",
            f"-imgFile={scene.parents[0] / 'render' / scene.stem}.png"
        ]

        chunks = list()

        for frame in range(frame_range[0], frame_range[1] - frame_padding, frame_padding):
            end_frame = frame + frame_padding - 1
            chunks.append((frame, end_frame))

        rest = frame_range[1] % frame_padding
        if rest:
            chunks.append((frame_range[1] - rest, frame_range[1]))

        for start, end in chunks:
            logger.info(f"Creating a new task with frames: {start} {end}")
            job.newTask(title=f"frames={start}-{end}", argv = arg_list + [f"-frames={start}-{end}"], service="TD_TEST_107")
        
        cmd = ' '.join(arg_list)
        logger.info("Launching command: " + cmd)

        jid = job.spool()
        logger.info(f"Created job: {jid}")
