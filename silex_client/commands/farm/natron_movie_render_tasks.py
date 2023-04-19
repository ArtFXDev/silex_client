from __future__ import annotations

import logging
import typing
from typing import Any, Dict
from pathlib import Path

from fileseq import FrameSet
from silex_client.commands.farm.deadline_render_task import DeadlineRenderTaskCommand
from silex_client.action.command_base import CommandBase
from silex_client.utils.deadline.runner import DeadlineRunner
from silex_client.utils.parameter_types import IntArrayParameterMeta

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
            "hide": True
        },
        "movie": {
            "label": "Generate a movie by job",
            "type": bool,
            "value": False,
            "hide": False
        },
        "resolution": {
            "label": "Resolution movie (width, height)",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
            "hide": True,
        }
    }

    async def setup(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        # hide resolution if movie is not true
        resolution = self.command_buffer.parameters.get('resolution')
        is_movie = self.command_buffer.parameters.get('movie')
        if not is_movie.get_value(action_query):
            resolution.hide = True
        else:
            resolution.hide = False



    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        """
        If movies are asked, submits a movie_job for each render jobs.
        """

        # run movie
        if parameters.get('movie'):
            # Submit to Deadline Runner
            dr = DeadlineRunner()
            context = action_query.context_metadata

            for job in parameters.get('jobs'):

                # set up command
                username = job.job_info.get('UserName')
                project = context.get('project').lower()
                seq = context.get('sequence')
                shot = context.get('shot')
                res = f"{parameters.get('resolution')[0]},{parameters.get('resolution')[1]}"
                filename = job.job_info.get('Name')
                task = f"{context.get('task')}_{filename}"

                root = Path(job.output_path).parent
                ext = Path(job.output_path).suffix
                padding = "#" * len(str(job.frame_range.end()))
                frame = f"{Path(job.output_path).stem}.{padding}{ext}"
                movie_name = f"{Path(job.output_path).stem}_movie.mp4"
                inp = root / frame
                out = root / movie_name

                argument_cmd = f"overlay --username {username} --filename {filename} --project {project} --task {task} --seq {seq} --shot {shot} --res {res} {inp} {out}"

                # set up job_movie
                job_movie = CommandLineJob(
                    job_title=f"{filename}_movie",
                    user_name=username,
                    frame_range=FrameSet('1'),
                    command=argument_cmd,
                    rez_requires="silex_natron",
                    batch_name=job.job_info.get('BatchName'),
                    output_path=str(root / movie_name),
                    is_single_frame=True
                )
                job_movie.set_dependency(job.id)
                job_movie.set_group(job.job_info.get('Group'))
                job_movie.set_pool(job.job_info.get('Pool'))
                job_movie.set_chunk_size(job.job_info.get('ChunkSize'))
                job_movie.set_priority(job.job_info.get('Priority'))

                # run job
                dr.run(job_movie)
