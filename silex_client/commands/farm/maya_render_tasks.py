from __future__ import annotations

import logging
import pathlib
import typing
from pprint import pformat
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.frames import split_frameset
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
            "type": FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            'label': "Task Size",
            "type": int,
            "value": 5
        },
        "keep_output_type": {
            "label": "Keep output type specified in the scene",
            "type": bool,
            "value": False,
        },
        "render_layers": {
            "label": "Seperate Render layers",
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
        flog.info(f'scene path:{parameters["scene_file"]}')
        scene: pathlib.Path = parameters["scene_file"]
        # Deadline resolves M:/testpipe as //tars/tespipetestpipe, changed to // to ensure it resolves as \\tars\\testpipe\\testpipe
        # scene = pathlib.Path(scene.as_posix().replace('/', '//'))
        keep_output_type: bool = parameters["keep_output_type"]

        project = (
            action_query.context_metadata["project"].lower()
            if "project" in action_query.context_metadata
            else None
        )

        # Build the Maya command
        maya_cmd = (
            command_builder.CommandBuilder(
                "Render",
                rez_packages=["maya", project],
                delimiter=" ",
                dashes="-",
            )
            .param("r", parameters["renderer"])
            .param(
                "rd",
                parameters["output_folder"],
                # parameters["output_folder"].as_posix().replace('/','//'),
            )

        )

        if not keep_output_type:
            maya_cmd.param("of", parameters["output_extension"])

        # Renderer specific options (arnold, vray...)
        if parameters["renderer"] == "arnold":
            maya_cmd.param(
                "skipExistingFrames", str(parameters["skip_existing"]).lower()
            )
            maya_cmd.param("ai:lve", 2)  # log level
            maya_cmd.param("ai:device", parameters['arnold_device'])
            maya_cmd.param("ai:alf", "true")  # Abort on license fail
            maya_cmd.param("ai:aerr", "true")  # Abort on error
            maya_cmd.param("fnc", 3)  # File naming name.#.ext
        elif parameters["renderer"] == "vray":
            # Skip existing frames is a different flag
            # See: https://forums.autodesk.com/t5/maya-forum/maya-batch-with-render-skipexistingframes/td-p/11117913
            maya_cmd.param("rep", 0 if parameters["skip_existing"] else 1)

        # Deadline frame variable substitution
        maya_cmd.param("s", "<STARTFRAME>")
        maya_cmd.param("e", "<ENDFRAME>")

        render_layers = []
        for render_layer in parameters["render_layers"]:
            render_layers.append(render_layer)
        maya_cmd.param("rl", render_layers)
        output_filename = f"{parameters['output_filename']}"
        maya_cmd.param("im", output_filename)
        maya_cmd.value(scene.as_posix())
        # maya_cmd.value(scene.as_posix().replace('/', '//'))

        # Command:
        # cmd = "rez env maya testpipe -- Render -r arnold -rd M:/testpipe/shots/s01/p010/lighting_main/publish/v000/exr/render -of exr -skipExistingFrames true -ai:lve 2 -ai:device 0 -ai:alf true -ai:aerr true -fnc 3 -im testpipe_s01_p010_lighting_main_publish_v000_render_defaultRenderLayer -rl defaultRenderLayer -s 1 -e 10 M:/testpipe/shots/s01/p010/lighting_main/publish/v000/ma/main/testpipe_s01_p010_lighting_main_publish_v000_main.ma

        return {"command": maya_cmd,
                "file_name": scene.stem,
                "frame_range": parameters["frame_range"].frameRange(),
                "task_size": parameters["task_size"]}
