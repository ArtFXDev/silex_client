from __future__ import annotations

import logging
import os
from pathlib import Path
import typing
from typing import Any, Dict, List, cast
import fileseq

from silex_client.commands.farm.deadline_render_task import DeadlineRenderTaskCommand
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import ArnoldJob


class KickRenderTasksCommand(DeadlineRenderTaskCommand):
    """
    Construct Arnold Deadline Job.
    """
    parameters = {
        "ass_folders": {
            "label": "Select Ass folders (render layers)",
            "type": TaskFileParameterMeta(
                extensions=[".ass"], directory=True, multiple=True
            ),
        },
        "frame_range": {
            "label": "Frame range",
            "type": fileseq.FrameSet,
            "value": "1001-1050x1",
        },
        "output_path": {"type": Path, "value": "", "hide": True},
    }

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        ass_folders: List[Path] = parameters["ass_folders"]
        output_path: Path = parameters["output_path"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        rez_requires: str = "arnold " + cast(str, action_query.context_metadata["project"]).lower()
        user_name: str = cast(str, action_query.context_metadata["user"]).lower().replace(' ', '.')

        # List other ass files in dir
        ass_files = [
            f for f in os.listdir(ass_folders[0]) if Path(str(f)).suffix == ".ass"
        ]

        jobs = []

        # for each render layer:
        for ass_folder in ass_folders:
            ass_files = [
                f for f in os.listdir(ass_folder) if Path(f).suffix == ".ass"
            ]

            # use first file of sequence, Arnold find the rest of the sequence
            file_path: Path = ass_folder.joinpath(str(ass_files[0]))
            file_path = file_path.as_posix()
            publish_name = file_path.split("/")[9]
            folder_name = publish_name + "_" + ass_folder.stem

            output_filename: str = f"{output_path.stem}_{folder_name}{''.join(output_path.suffixes)}"

            output_dir: Path = (
                            output_path.parent
                            / folder_name
                            )

            plugin_output_path: str = output_dir.as_posix() + "/" + output_filename

            create_dir(str(output_dir), folder_name)

            # get job_title and batch_name
            names = self.define_job_names(plugin_output_path)
            job_title = names.get("job_title")
            batch_name = names.get("batch_name")

            job = ArnoldJob(
                job_title,
                user_name,
                frame_range,
                str(file_path),
                plugin_output_path,
                batch_name=batch_name,
                rez_requires=rez_requires
            )

            jobs.append(job)

        return {"jobs": jobs}

def create_dir(path, folder):
    path_split = path.split("\\")

    tars_path = "\\\\tars/" + path_split[1]
    ana_path = "\\\\ana/" + path_split[1]
    if os.path.isdir(tars_path):
        path_split[0] = tars_path
    if os.path.isdir(ana_path):
        path_split[0] = ana_path

    path_create = "/".join(path_split[0:-1]) + "/" + folder
    if not os.path.isdir(path_create):
        os.mkdir(path_create)
