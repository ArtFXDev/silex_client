from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast

from fileseq import FrameSet
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


class VrayRenderTasksCommand(CommandBase):
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
            "value": "1-50x1",
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
        },
        "publish_folder":{
            "label" : "Create a folder by render layer (disable if a vrscene by frame)",
            "type": bool,
            "value": True,
            "hide": False
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
        vrscenes: List[pathlib.Path] = parameters["vrscenes"]
        output_directory: pathlib.Path = parameters["output_directory"]
        output_filename: str = parameters["output_filename"]
        output_extension: str = parameters["output_extension"]
        frame_range: FrameSet = parameters["frame_range"]
        publish_folder = parameters["publish_folder"]
        user_name: str = cast(str, action_query.context_metadata["user"]).lower().replace(' ', '.')
        rez_requires: str = "vray " + cast(str, action_query.context_metadata["project"]).lower()
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int]

        if parameter_overrides:
            resolution = parameters["resolution"]
        else:
            resolution = None

        jobs = []

        # One Vrscene file per render layer
        for vrscene in vrscenes:

            file_path = vrscene.as_posix()

            # Detect the render layer name from the parent folder
            split_by_name = vrscene.stem.split(f"{vrscene.parents[0].stem}_")

            if len(split_by_name) > 1:
                layer_name = split_by_name[-1]
            else:
                # Otherwise take the filename
                layer_name = vrscene.stem

            publish_name = file_path.split("/")[9]

            folder_name = publish_name
            if publish_folder:
                folder_name = publish_name + "_" + layer_name

            output_path = (
                    output_directory
                    / folder_name
                    / f"{output_filename}_{folder_name}.{output_extension}"
            ).as_posix()


            job = VrayJob(
                user_name,
                frame_range,
                file_path,
                output_path,
                resolution,
                rez_requires=rez_requires
            )

            jobs.append(job)

        return {"jobs": jobs}
