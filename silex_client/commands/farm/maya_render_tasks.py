from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import (
    MultipleSelectParameterMeta,
    SelectParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class MayaRenderTasksCommand(CommandBase):
    """
    Construct Maya render commands
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".ma", ".mb"]),
        },
        "renderer": {
            "label": "Renderer",
            "type": SelectParameterMeta("vray", "arnold"),
            "value": "vray",
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
        "keep_output_type": {
            "label": "Keep output type specified in the scene",
            "type": bool,
            "value": False,
        },
        "render_layers": {
            "label": "Render layers",
            "type": MultipleSelectParameterMeta(),
        },
        "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "output_folder": {"type": pathlib.Path, "hide": True, "value": ""},
        "output_filename": {"type": str, "hide": True, "value": ""},
        "output_extension": {"type": str, "hide": True, "value": "exr"},
    }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Get value of frame range
        self.command_buffer.parameters[
            "frame_range"
        ].value = self.command_buffer.parameters["frame_range"].get_value(action_query)

        # Fill render layer parameter
        if not action_query.store.get("get_maya_render_layer"):
            try:
                import maya.cmds as cmds

                render_layers: List[str] = cmds.ls(type="renderLayer")

                # Exclude layers in references
                render_layers = [rl for rl in render_layers if not ":" in rl]

                self.command_buffer.parameters["render_layers"].rebuild_type(
                    *render_layers
                )
                self.command_buffer.parameters["render_layers"].value = render_layers
                action_query.store["get_maya_render_layer"] = True
            except:
                self.command_buffer.parameters["render_layers"].type = str

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        keep_output_type: bool = parameters["keep_output_type"]
        task_size: int = parameters["task_size"]

        # Build the Maya command
        maya_cmd = (
            command_builder.CommandBuilder(
                "Render",
                rez_packages=["maya", action_query.context_metadata["project"].lower()],
                delimiter=" ",
                dashes="-",
            )
            .param("r", parameters["renderer"])
            .param("rd", parameters["output_folder"].as_posix())
        )

        if not keep_output_type:
            maya_cmd.param("of", parameters["output_extension"])

        # Renderer specific options (arnold, vray...)
        if parameters["renderer"] == "arnold":
            maya_cmd.param(
                "skipExistingFrames", str(parameters["skip_existing"]).lower()
            )
            maya_cmd.param("ai:lve", 2)  # log level
            maya_cmd.param("fnc", 3)  # File naming name.#.ext
        elif parameters["renderer"] == "vray":
            # Skip existing frames is a different flag
            # See: https://forums.autodesk.com/t5/maya-forum/maya-batch-with-render-skipexistingframes/td-p/11117913
            maya_cmd.param("rep", 0 if parameters["skip_existing"] else 1)

        tasks: List[farm.Task] = []

        # Split frame range since Maya only accepts start, end and step frames
        # Ex: 5-10,3,17-180 -> [5-10, 3, 17-180]
        #     With a task size of 2: [5-6, 7-8, 9-10, 3, 17-18...]
        patterns = parameters["frame_range"].frameRange().split(",")
        frame_chunks: List[FrameSet] = []

        for pattern in patterns:
            pattern_frames = FrameSet(pattern)

            # Split sub pattern of frames by task size
            if len(pattern_frames) > 1:
                frame_chunks.extend(split_frameset(pattern_frames, task_size))
            else:
                frame_chunks.append(pattern_frames)

        # Create subtasks for each render layer
        for render_layer in parameters["render_layers"]:
            render_layer_task = farm.Task(title=render_layer)

            # Add render layer to the image name
            output_filename = f"{parameters['output_filename']}_{render_layer}"

            # Creating tasks for each frame chunk
            for chunk in frame_chunks:
                chunk_cmd = maya_cmd.deepcopy()

                chunk_cmd.param("im", output_filename)
                chunk_cmd.param("rl", render_layer)

                # Frame range start, end
                chunk_cmd.param("s", chunk.start())
                chunk_cmd.param("e", chunk.end())

                # Add the scene file
                chunk_cmd.value(scene.as_posix())

                task = farm.Task(title=str(chunk))

                task.addCommand(
                    farm.wrap_with_mount(
                        chunk_cmd, action_query.context_metadata["project_nas"]
                    )
                )

                if len(parameters["render_layers"]) > 1:
                    render_layer_task.addChild(task)
                else:
                    tasks.append(task)

            if len(parameters["render_layers"]) > 1:
                tasks.append(render_layer_task)

        return {"tasks": tasks, "file_name": scene.stem}
