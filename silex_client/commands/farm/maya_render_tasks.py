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
    IntArrayParameterMeta,
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
        "render_specific_frames": {
            "label": "Render specific frames",
            "type": bool,
            "value": False,
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": IntArrayParameterMeta(3),
            "value": [1, 50, 1],
        },
        "specific_frames_frameset": {
            "label": "Specific frames",
            "type": FrameSet,
            "value": "1,15,180",
            "hide": True,
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
        specific_frames = parameters["render_specific_frames"]

        self.command_buffer.parameters[
            "specific_frames_frameset"
        ].hide = not specific_frames

        self.command_buffer.parameters["frame_range"].hide = specific_frames
        self.command_buffer.parameters["task_size"].hide = specific_frames

        if not action_query.store.get("get_maya_render_layer"):
            try:
                import maya.cmds as cmds

                render_layers: List[str] = cmds.ls(type="renderLayer")
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
        frame_range: List[int] = parameters["frame_range"]
        task_size: int = parameters["task_size"]

        # Build the Blender command
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

        # Renderer specific options
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
        chunk_render = not parameters["render_specific_frames"]

        if chunk_render:
            # Split frames by task size
            frame_chunks = split_frameset(
                FrameSet.from_range(frame_range[0], frame_range[1], frame_range[2]),
                task_size,
            )
        else:
            # Otherwise split framesets and take them individually
            patterns = str(parameters["specific_frames_frameset"]).split(",")
            frame_chunks = [FrameSet(pattern) for pattern in patterns]

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

                chunk_cmd.param("s", chunk.start())
                chunk_cmd.param("e", chunk.end())
                chunk_cmd.param("b", frame_range[2])

                # Add the scene file
                chunk_cmd.value(scene.as_posix())

                task = farm.Task(title=chunk.frameRange(), argv=chunk_cmd.as_argv())
                task.add_mount_command(action_query.context_metadata["project_nas"])

                if len(parameters["render_layers"]) > 1:
                    render_layer_task.addChild(task)
                else:
                    tasks.append(task)

            if len(parameters["render_layers"]) > 1:
                tasks.append(render_layer_task)

        return {"tasks": tasks, "file_name": scene.stem}
