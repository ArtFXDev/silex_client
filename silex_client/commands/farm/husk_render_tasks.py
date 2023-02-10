from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    TaskFileParameterMeta,
    SelectParameterMeta
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import DeadlineHuskJob
from silex_client.utils.log import flog

class HuskRenderTasksCommand(CommandBase):
    """
    Construct Husk render commands
    See: https://www.sidefx.com/docs/houdini/ref/utils/husk.html
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".usd", ".usda", ".usdc"], multiple=True),
        },
        "frame_range": {
            "label": "Frame range",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": False,
            "hide": True,  # Until fixed
        },
        "LOG_level":{
            "labem": "LOG Level",
            "type": SelectParameterMeta(0, 1, 2, 3, 4, 5, 6),
            "value": 0
        },
        "output_directory": {
            "type": pathlib.Path,
            "hide": True,
            "value": ""
        },
        "output_filename": {
            "type": pathlib.Path,
            "hide": True,
            "value": ""
        },
        "output_extension": {
            "type": str,
            "hide": True,
            "value": "exr"
        }
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        '''
        scene: pathlib.Path = parameters["scene_file"]
        full_path = f"\{(parameters['output_directory'] / parameters['output_filename']).as_posix()}.$F4.{parameters['output_extension']}"



        ##### BUILD HUSK COMMAND
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
        frame_range_split = frame_range.split("x")

        if len(frame_range_split) == 2:
            increment = frame_range[0].split("x")[-1]
            husk_cmd.param("frame-inc", increment)
            husk_cmd.param("frame-count", 1)
        else:
            task_size: int = parameters["task_size"]
            task_size = str(task_size)
            husk_cmd.param("frame-count", task_size)

        husk_cmd.param("frame", "<STARTFRAME>")

        #### BUILD DEADLINE JOBS
        context = action_query.context_metadata
        user = context["user"].lower().replace(' ', '.')
        cmd = str(husk_cmd).split(' ', 1)[1]

        flog.info(f"cmd : {cmd}")
        '''

        jobs=[]

        files = parameters["scene_file"]
        flog.info(f"files : {files}, type : {type(files)}")

        for file in files:
            scene: pathlib.Path = file
            flog.info(parameters['output_directory'])
            flog.info(parameters['output_filename'].as_posix())
            usd_name = str(scene).split("_")[-1].split(".")[0]
            full_path = (
                parameters['output_directory']
                / usd_name
                / f"{parameters['output_filename']}_{usd_name}.$F4.{parameters['output_extension']}"
            )
            """
            f"\{(parameters['output_directory'] / 
                            usd_name /
                            parameters['output_filename']).as_posix()}.$F4.{parameters['output_extension']}"
            """
            flog.info(f"full_path : {full_path}, type : {type(full_path)}")

            project = cast(str, action_query.context_metadata["project"]).lower()
            flog.info(f"project : {project}, type : {type(project)}")

            context = action_query.context_metadata
            user = context["user"].lower().replace(' ', '.')
            flog.info(f"user : {user}, type : {type(user)}")

            log_level = parameters["LOG_level"]
            flog.info(f"LOG level : {log_level}, type: {type(log_level)}")

            job = DeadlineHuskJob(
                job_title=usd_name,
                user_name=user,
                scenefile_path=str(scene),
                outputfile_path=str(full_path),
                log_level=log_level,
                frame_range=parameters["frame_range"],
                rez_requires=f"husk {project}",
                batch_name=str(parameters['output_directory'])
            )

            jobs.append(job)

        return {"jobs" : jobs}
