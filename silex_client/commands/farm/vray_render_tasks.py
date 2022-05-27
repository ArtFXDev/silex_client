from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm, frames
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    RadioSelectParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


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
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True,
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
        },
        "resolution": {
            "label": "Resolution (width, height)",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
            "hide": True,
        },
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

        engine: int = parameters["engine"]
        frame_range: FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        skip_existing = int(parameters["skip_existing"])
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int] = parameters["resolution"]

        tasks: List[farm.Task] = []

        for vrscene in vrscenes:
            # Detect the render layer name from the parent folder
            split_by_name = vrscene.stem.split(f"{vrscene.parents[0].stem}_")

            if len(split_by_name) > 1:
                layer_name = split_by_name[-1]
            else:
                # Otherwise take the filename
                layer_name = vrscene.stem

            full_output_path = (
                output_directory
                / layer_name
                / f"{output_filename}_{layer_name}.{output_extension}"
            )

            # Build the V-Ray command
            project = cast(str, action_query.context_metadata["project"]).lower()
            vray_cmd = command_builder.CommandBuilder(
                "vray",
                rez_packages=["vray", project],
            )
            vray_cmd.param("skipExistingFrames", skip_existing)
            vray_cmd.disable(["display", "progressUseColor", "progressUseCR"])
            vray_cmd.param("progressIncrement", 5)
            vray_cmd.param("verboseLevel", 3)
            vray_cmd.param("rtEngine", engine)
            vray_cmd.param("sceneFile", vrscene.as_posix())
            vray_cmd.param("imgFile", full_output_path.as_posix())

            if parameter_overrides:
                vray_cmd.param("imgWidth", resolution[0]).param(
                    "imgHeight", resolution[1]
                )

            render_layer_task = farm.Task(title=layer_name)
            frame_chunks = frames.split_frameset(frame_range, task_size)

            # Creating tasks for each frame chunk
            for chunk in frame_chunks:
                chunk_cmd = vray_cmd.deepcopy()

                chunk_cmd.param("frames", farm.frameset_to_frames_str(chunk))

                task = farm.Task(title=str(chunk))

                project_nas = cast(str, action_query.context_metadata["project_nas"])
                task.addCommand(farm.wrap_with_mount(chunk_cmd, project_nas))

                if len(vrscenes) > 1:
                    render_layer_task.addChild(task)
                else:
                    tasks.append(task)

            if len(vrscenes) > 1:
                tasks.append(render_layer_task)

        return {
            "file_name": vrscenes[0].stem,
            "tasks": tasks,
        }
