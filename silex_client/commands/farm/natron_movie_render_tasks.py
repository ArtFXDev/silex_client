from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List, cast
from pathlib import Path

from fileseq import FrameSet, FileSequence
from silex_client.commands.farm.deadline_render_task import DeadlineRenderTaskCommand
from silex_client.action.command_base import CommandBase
from silex_client.utils.deadline.runner import DeadlineRunner

from silex_client.utils.log import flog

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
from silex_client.utils.deadline.job import CommandLineJob


class SubmitNatronMoviesCommand(DeadlineRenderTaskCommand):
    """
    Construct Natron Movie commands
    """

    parameters = {
        "jobs": {
            "type": list,
            # "type": ListParameterMeta(AnyParameter),
            "hide": True
        },
    }

    async def setup(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        pass

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        context = action_query.context_metadata

        user_name: str = cast(str, context["user"]).lower().replace(' ', '.')

        rez_requires: str = f"silex_natron {str(context['project']).lower()}"

        argument_pattern = "overlay --username {username} --filename {filename} --project {project} --task {task} --seq {seq} --shot {shot} {input} {output}"
        # argument_pattern = "overlay {input} {output}"

        # root = Path("M:/testpipe/shots/s01/p010/lighting_hou_vray/publish/v000/exr/render/temp_firemen_test")
        # frame = "firemen_s01_p010_lighting_main_publish_v000_render.####.exr"
        # movie_name = "firemen_s01_p010_lighting_main_publish_v000_render.mp4"

        flog.info("Starting SubmitNatronMoviesCommand")
        flog.info(parameters["jobs"])

        common = {
            "username": user_name,
            "filename": "o.o",
            "project": context.get('project').lower(),
            "task": context.get('task').lower(),  # context.get('task_type').lower()
            "seq": context.get('sequence').lower(),
            "shot": context.get('shot').lower(),
            # "res": "1920,1080",  # TODO: fix in the tool
        }

        movie_jobs = []

        for job in parameters["jobs"]:

            id = job.id
            if not id:
                flog.error("Job has no id - needs id from submission for dependency. Skipped.")
                continue

            seq = FileSequence(job.output_path)
            # FIXME: movie extension to user choice
            if seq.padding():
                source = seq.frame("####")
                destination = seq.format(template='{dirname}{basename}mp4')
            else:
                source = seq.format(template='{dirname}{basename}.####{extension}')
                destination = seq.format(template='{dirname}{basename}.mp4')

            flog.info(job.output_path)
            flog.info(source)
            flog.info(destination)

            data = common.copy()
            data["input"] = source
            data["output"] = destination

            argument_cmd = argument_pattern.format(**data)

            movie_job = CommandLineJob(
                job_title=str(Path(destination).stem),
                user_name=user_name,
                frame_range=FrameSet("1"),
                command=argument_cmd,
                rez_requires=rez_requires,
                batch_name=job.batch_name,
                output_path=str(Path(source).parent),
                is_single_frame=True
            )

            movie_job.set_dependency(id)

            # Submit to Deadline Runner
            dr = DeadlineRunner()
            dr.run(movie_job)
            movie_jobs.append(movie_job)
            flog.info(movie_job)

        # return {"jobs": movie_jobs}
