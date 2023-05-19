from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, cast

from fileseq import FrameSet

from silex_client.commands.farm.deadline_render_task import DeadlineRenderTaskCommand
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    TaskFileParameterMeta,
    SelectParameterMeta
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import HuskJob


class HuskRenderTasksCommand(DeadlineRenderTaskCommand):
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
            "value": "1001-1050x1",
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": False,
            "hide": True,  # Until fixed
        },
        "LOG_level": {
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
        jobs = []

        files = parameters["scene_file"]

        # for each files
        for file in files:
            # paths
            scene: pathlib.Path = file
            folder_name = str(file.parent.stem)
            full_path = (
                    parameters['output_directory']
                    / folder_name
                    / f"{parameters['output_filename']}_{folder_name}.$F4.{parameters['output_extension']}"
            )
            project = cast(str, action_query.context_metadata["project"]).lower()

            # user
            context = action_query.context_metadata
            user = context["user"].lower().replace(' ', '.')

            # job_title and batch_name
            job_title = folder_name
            batch_name = self.get_batch_name(context)

            # log
            log_level = parameters["LOG_level"]

            # create job
            job = HuskJob(
                job_title=job_title,
                user_name=user,
                frame_range=parameters["frame_range"],
                file_path=str(scene),
                output_path=str(full_path),
                log_level=log_level,
                batch_name=batch_name,
                rez_requires=f"karma {project}"
            )

            jobs.append(job)

        return {"jobs": jobs}
