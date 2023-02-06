from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast
from silex_client.utils.log import flog

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class HuskRenderTasksCommand(CommandBase):
    """
    Construct Husk render commands
    See: https://www.sidefx.com/docs/houdini/ref/utils/husk.html
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".usd", ".usda", ".usdc"]),
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            #"type": IntArrayParameterMeta(3),
            #"value": [1, 50, 1],
            "type": FrameSet,
            "value": "1-50x1",
        },
        #"output_directory": {"type": pathlib.Path, "hide": True, "value": ""},
        #"output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        #"output_extension": {"type": str, "hide": True, "value": "exr"},
        "output_directory": {"type": pathlib.Path, "hide": False, "value": ""},
        "output_filename": {"type": pathlib.Path, "hide": False, "value": ""},
        "output_extension": {"type": str, "hide": False, "value": "exr"},
        "task_size" : {
            "label": "Task Size",
            "type": int,
            "value" : 10
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]

        full_path = f"\{(parameters['output_directory'] / parameters['output_filename']).as_posix()}.$F4.{parameters['output_extension']}"

        husk_cmd = command_builder.CommandBuilder(
            "husk",
            rez_packages=["houdini", action_query.context_metadata["project"].lower()],
            delimiter=" ",
            dashes="--",
        )
        husk_cmd.param("usd-input", scene.as_posix())
        husk_cmd.param("output", full_path)
        husk_cmd.param("make-output-path")
        husk_cmd.param("exrmode", 1)
        husk_cmd.param("verbose", "3a")

        #set cmd frames
        frame_range: List[int] = parameters["frame_range"]
        frame_range = str(frame_range)
        increment = frame_range[0].split("x")[-1]
        task_size: int = parameters["task_size"]
        task_size = str(task_size)



        husk_cmd.param("frame", "<STARTFRAME>")
        flog.info("add frame param")
        husk_cmd.param("frame-inc", increment)
        flog.info("add frame increment")
        husk_cmd.param("frame-count", task_size)
        flog.info("add frame count")

        flog.info(husk_cmd)
        return {"command": husk_cmd, "file_name": scene.stem, "frame_range": parameters["frame_range"].frameRange()}
