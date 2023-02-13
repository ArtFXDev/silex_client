from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List, cast
import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils.log import flog
from silex_client.utils.parameter_types import (
    EditableListParameterMeta,
    MultipleSelectParameterMeta,
    PathParameterMeta,
    RadioSelectParameterMeta,
    SelectParameterMeta,
    TaskFileParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from silex_client.utils.deadline.job import DeadlineMayaBatchJob, DeadlineCommandLineJob


class MayaRenderTasksCommand(CommandBase):
    """
    Construct Maya render commands
    """

    parameters = {
        "scene_file_out_of_pipeline": {"type": bool, "value": False, "hide": True},
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".ma", ".mb"]),
        },
        "renderer": {
            "label": "Renderer",
            "type": SelectParameterMeta("vray", "arnold"),
            "value": "vray",
        },
        "arnold_device": {
            "label": "Render device",
            "type": RadioSelectParameterMeta(
                **{
                    "CPU": 0,
                    "GPU": 1,
                }
            ),
        },
        "frame_range": {
            "label": "Frame range",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "keep_output_type": {
            "label": "Keep output type specified in the scene",
            "type": bool,
            "value": False,
        },
        "render_layers": {
            "label": "Separate Render layers",
            "type": MultipleSelectParameterMeta(),
        },
        "output_path": {"type": pathlib.Path, "value": "", "hide": True}
    }

    async def setup(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        if parameters["scene_file_out_of_pipeline"]:
            flog.info("scene_file")
            flog.info(self.command_buffer.parameters["scene_file"])
            self.command_buffer.parameters["scene_file"].type = PathParameterMeta(
                [".ma", ".mb"]
            )

        # Get value of frame range
        self.command_buffer.parameters[
            "frame_range"
        ].value = self.command_buffer.parameters["frame_range"].get_value(action_query)

        self.command_buffer.parameters["arnold_device"].hide = (
                parameters["renderer"] != "arnold"
        )

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

            except:
                self.command_buffer.parameters[
                    "render_layers"
                ].type = EditableListParameterMeta(str)

                self.command_buffer.parameters["render_layers"].value = [
                    "defaultRenderLayer",
                ]

            action_query.store["get_maya_render_layer"] = True

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        file_path: pathlib.Path = parameters["scene_file"]
        output_path: pathlib.Path = parameters["output_path"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        rez_requires: str = "maya " + cast(str, action_query.context_metadata["project"]).lower()
        user_name: str = cast(str, action_query.context_metadata["user"]).lower().replace(' ', '.')
        job_title: str = file_path.stem

        jobs = []

        job = DeadlineMayaBatchJob(
            job_title,
            user_name,
            frame_range,
            rez_requires,
            file_path.as_posix(),
            output_path.as_posix(),
            parameters['renderer']
        )

        jobs.append(job)

        return {"jobs": jobs}
