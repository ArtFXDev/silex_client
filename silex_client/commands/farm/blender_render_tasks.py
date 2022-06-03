from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.farm import Task
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    RadioSelectParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BlenderRenderTasksCommand(CommandBase):
    """
    Construct Blender render commands
    See: https://docs.blender.org/manual/en/dev/advanced/command_line/arguments.html
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".blend"]),
        },
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
        "output_directory": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_extension": {"type": str, "hide": True, "value": "exr"},
        "multi_layer_exr": {
            "label": "Export Multi-Layer EXR",
            "type": bool,
            "hide": True,
            "value": False,
        },
        "engine": {
            "label": "Render engine",
            "type": RadioSelectParameterMeta(
                **{"Cycles": "CYCLES", "Evee": "BLENDER_EEVEE"}
            ),
        },
        "cycles-device": {
            "label": "Cycles device",
            "type": RadioSelectParameterMeta(
                **{k: k for k in ["CPU", "CUDA", "OPTIX", "CUDA+CPU", "OPTIX+CPU"]}
            ),
        },
    }

    EXTENSIONS_MAPPING = {"exr": "OPEN_EXR", "png": "PNG", "jpg": "JPG", "tiff": "TIFF"}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        self.command_buffer.parameters["multi_layer_exr"].hide = (
            not parameters["output_extension"] == "exr"
        )

        self.command_buffer.parameters["cycles-device"].hide = (
            not parameters["engine"] == "CYCLES"
        )

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        frame_range: FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        output_extension = self.EXTENSIONS_MAPPING[parameters["output_extension"]]

        if parameters["output_extension"] == "exr" and parameters["multi_layer_exr"]:
            output_extension = "OPEN_EXR_MULTILAYER"

        # Build the Blender command
        project = cast(str, action_query.context_metadata["project"]).lower()
        blender_cmd = command_builder.CommandBuilder(
            "blender",
            rez_packages=["blender", project],
            delimiter=" ",
            dashes="--",
        )
        blender_cmd.param("background")
        blender_cmd.value("-noaudio")

        # Scene file
        blender_cmd.value(scene.as_posix())

        blender_cmd.param("render-format", output_extension)
        blender_cmd.param("engine", parameters["engine"])

        output_path = (
            parameters["output_directory"] / f"{parameters['output_filename']}.####"
        )
        output_file = (output_path).as_posix()
        blender_cmd.param("render-output", output_file)
        blender_cmd.param("log-level", 0)

        tasks: List[Task] = []

        # Split frames by task size
        frame_chunks = split_frameset(frame_range, task_size)

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = blender_cmd.deepcopy()

            # Add the frames argument
            chunk_cmd.param("render-frame", farm.frameset_to_frames_str(chunk, sep=","))

            if parameters["engine"] == "CYCLES":
                # See: https://docs.blender.org/manual/en/latest/advanced/command_line/render.html#cycles
                chunk_cmd.value("--")
                chunk_cmd.param("cycles-device", parameters["cycles-device"])

            # Create the task
            task = Task(title=str(chunk))

            command = farm.wrap_command(
                [
                    farm.get_mount_command(
                        action_query.context_metadata["project_nas"]
                    ),
                    farm.get_clear_frames_command(
                        pathlib.Path(parameters["output_directory"]), chunk
                    ),
                ],
                cmd=farm.Command(chunk_cmd.as_argv()),
            )
            task.addCommand(command)

            tasks.append(task)

        return {"tasks": tasks, "file_name": scene.stem}
