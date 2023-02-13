from __future__ import annotations

import logging
import os
import pathlib
import typing
from typing import Any, Dict, List, cast

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm, frames
from silex_client.utils.parameter_types import TaskFileParameterMeta, SelectParameterMeta
from silex_client.utils.log import flog

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import DeadlineArnoldJob


class KickRenderTasksCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "ass_folders": {
            "label": "Select Ass folders (render layers)",
            "type": TaskFileParameterMeta(
                extensions=[".ass"], directory=True, multiple=True
            ),
        },
        "use_xgen": {
            "label": "Use XGen",
            "type": bool,
            "value": False,
        },
        "use_mtoa": {
            "label": "Use Maya shaders (MtoA)",
            "type": bool,
            "value": False,
        },
        "frame_range": {
            "label": "Frame range",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True,
            "hide": True
        },
        "output_path": {"type": pathlib.Path, "value": "", "hide": True},
    }

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        ass_folders: List[pathlib.Path] = parameters["ass_folders"]
        output_path: pathlib.Path = parameters["output_path"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]

        # List other ass files in dir
        ass_files = [
            f for f in os.listdir(ass_folders[0]) if pathlib.Path(f).suffix == ".ass"
        ]

        tmp = pathlib.Path(str(ass_files[0]))
        batch_name = tmp.stem.rsplit('_', 1)[0]

        jobs = []

        # for each render layer:
        for ass_folder in ass_folders:
            ass_files = [
                f for f in os.listdir(ass_folder) if pathlib.Path(f).suffix == ".ass"
            ]

            # pass 1st file of sequence, Arnold find the rest of the sequence
            scenefile_path = ass_folder.joinpath(str(ass_files[0]))

            output_filename = f"{output_path.stem}_{ass_folder.stem}{''.join(output_path.suffixes)}"

            output_dir = output_path.parent

            plugin_output_path = str(output_dir) + output_filename

            job_title = ass_folder.stem

            context = action_query.context_metadata
            user_name = cast(str, context["user"]).lower().replace(' ', '.')

            rez_requires = "arnold " + cast(str, action_query.context_metadata["project"]).lower()

            job = DeadlineArnoldJob(
                job_title,
                user_name,
                frame_range,
                rez_requires,
                scenefile_path.as_posix(),
                plugin_output_path,
                batch_name=batch_name
            )

            jobs.append(job)

        return {"jobs": jobs}
