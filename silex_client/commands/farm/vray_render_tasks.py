from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast
import os
from pathlib import Path

from fileseq import FrameSet
from silex_client.commands.farm.deadline_render_task import DeadlineRenderTaskCommand
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    RadioSelectParameterMeta,
    TaskFileParameterMeta,
)

from silex_client.utils.log import flog

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
from silex_client.utils.deadline.job import VrayJob


class VrayRenderTasksCommand(DeadlineRenderTaskCommand):
    """
    Construct V-Ray render commands
    """

    parameters = {
        "vrscenes": {
            "label": "Scene file(s) (You can select multiple render layers)",
            "type": TaskFileParameterMeta(multiple=True, extensions=[".vrscene"]),
        },
        "output_directory": {"type": pathlib.Path, "hide": True},
        "output_filename": {"type": str, "hide": True},
        "output_extension": {"type": str, "hide": True},
        "frame_range": {
            "label": "Frame range",
            "type": FrameSet,
            "value": "1001-1050x1",
        },
        "engine": {
            "label": "RT engine",
            "type": RadioSelectParameterMeta(
                **{"Regular": 0, "GPU CUDA": 5, "GPU RTX": 7}
            ),
            "value": 0,
        },
        "parameter_overrides": {
            "type": bool,
            "label": "Parameter overrides",
            "value": False,
            "hide": True
        },
        "resolution": {
            "label": "Resolution (width, height)",
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
        # Overriding resolution is optional
        hide_overrides = not parameters["parameter_overrides"]
        self.command_buffer.parameters["resolution"].hide = hide_overrides

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        context = action_query.context_metadata
        #flog.info(f"parameters = {action_query.parameters}")
        #flog.info(f"commands = {action_query.commands}")
        #flog.info(f"steps = {action_query.steps}")
        #flog.info(f"store = {action_query.store}")
        #flog.info(f"status = {action_query.status}")
        #flog.info(f"name = {action_query.name}")
        #flog.info(f"execution_type = {action_query.execution_type}")
        #flog.info(f"current_command_index = {action_query.current_command_index}")
        #flog.info(f"current_command = {action_query.current_command}")
        #flog.info(f"is_running = {action_query.is_running}")

        vrscenes: List[pathlib.Path] = parameters["vrscenes"]
        output_directory: pathlib.Path = parameters["output_directory"]
        output_filename: str = parameters["output_filename"]
        output_extension: str = parameters["output_extension"]
        frame_range: FrameSet = parameters["frame_range"]
        user_name: str = cast(str,context["user"]).lower().replace(' ', '.')
        rez_requires: str = "vray " + cast(str, context["project"]).lower()
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int]

        if parameter_overrides:
            resolution = parameters["resolution"]
        else:
            resolution = None

        jobs = []
        sequence = False

        # One Vrscene file per render layer
        for vrscene in vrscenes:

            flog.info(f"vrscene = {vrscene}")

            vr_files = []
            if os.path.isfile(vrscene):
                vr_files = [vrscene]
            else:
                vr_files = [
                    f for f in os.listdir(vrscene) if Path(f).suffix == ".vrscene"
                ]
                sequence = True

            # use first file of sequence, vray find the rest of the sequence
            file_path: Path = vrscene.joinpath(str(vr_files[0]))
            file_path = file_path.as_posix()

            # Detect the render layer name from the parent folder
            layer_name = ""
            if sequence :
                layer_name = vrscene.stem
            else:
                layer_name = str(vrscene.parents[0].stem)

            # build output path
            output_path = (
                    output_directory
                    / layer_name
                    / f"{output_filename}_{layer_name}.{output_extension}"
            ).as_posix()

            # get job_title and batch_name
            job_title = layer_name
            batch_name = self.get_batch_name(context)

            job = VrayJob(
                job_title,
                user_name,
                frame_range,
                file_path,
                output_path,
                sequence,
                batch_name=batch_name,
                resolution=resolution,
                rez_requires=rez_requires
            )

            jobs.append(job)

        return {"jobs": jobs}
