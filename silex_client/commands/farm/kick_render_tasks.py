from __future__ import annotations

import logging
import os
from pathlib import Path
import typing
from typing import Any, Dict, List, cast
from silex_client.utils.log import flog
import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import TaskFileParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import DeadlineArnoldJob


class KickRenderTasksCommand(CommandBase):
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
            "value": "1-50x1",
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

        tmp = Path(str(ass_files[0]))
        batch_name: str = tmp.stem.rsplit('_', 1)[0]

        jobs = []

        # for each render layer:
        for ass_folder in ass_folders:
            ass_files = [
                f for f in os.listdir(ass_folder) if Path(f).suffix == ".ass"
            ]

            # use first file of sequence, Arnold find the rest of the sequence
            file_path: Path = ass_folder.joinpath(str(ass_files[0]))

            output_filename: str = f"{output_path.stem}_{ass_folder.stem}{''.join(output_path.suffixes)}"

            output_dir: Path = output_path.parent

            plugin_output_path: str = str(output_dir) + output_filename

            job_title: str = ass_folder.stem

            job = DeadlineArnoldJob(
                job_title,
                user_name,
                frame_range,
                rez_requires,
                file_path.as_posix(),
                plugin_output_path,
                batch_name=batch_name
            )

            jobs.append(job)

        return {"jobs": jobs}
