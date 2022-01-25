from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils.command import CommandBuilder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import IntArrayParameterMeta, PathParameterMeta, SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os

class MantraCommand(CommandBase):
    """
    Construct Mantra Command
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": PathParameterMeta(extensions=[".hip", ".hipnc"]),
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "parameter_overrides": {
            "type": bool,
            "label": "Parameter overrides",
            "value": False,
        },
        "resolution": {
            "label": "Resolution ( width, height )",
            "type": IntArrayParameterMeta(2),
            "value": [1920, 1080],
            "hide": True,
        },
        "render_nodes": {
            "label": "Render Nodes",
            "type": SelectParameterMeta(),
            "value": None,
            "tooltip": "Select Render Mantra Node",
        }
    }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        hide_overrides = not parameters["parameter_overrides"]
        self.command_buffer.parameters["resolution"].hide = hide_overrides

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
        skip_existing = int(parameters["skip_existing"])
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int] = parameters["resolution"]

        """
        hou.hipFile.load('D:\mantra_render.hip');mantra=hou.node('/out/mantra1');hou.parm('/out/mantra1/trange').set(1);hou.parmTuple('/out/mantra1/f').deleteAllKeyframes();mantra.render()
        """
        # Build the mantra command
        mantra_cmd = CommandBuilder("hython3.7", rez_packages=["houdini"])
        mantra_cmd.param("-c", f"hou.hipFile.load({scene})")

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        if not os.isfile(scene):
            return

        get_mantra_nodes_cmd = CommandBuilder("hython3.7", rez_packages=["houdini"])
        str_cmd = f"hou.hipFile.load('{scene}');render_nodes=[rn.name() for rn in hou.node('/out').allSubChildren() if rn.type().name() == 'ifd'];print(render_nodes)"
        get_mantra_nodes_cmd.param("-c")
        mantra_render_nodes = [rn.name() for rn in hou.node("/out/").allSubChildren() if rn.type().name() is "ifd"]
        
        parameters["render_nodes"].type =  SelectParameterMeta(**mantra_render_nodes)

        """
        "hou.hipFile.load('D:\mantra_render.hip');render_nodes=[rn.name() for rn in hou.node('/out').allSubChildren() if rn.type().name() == 'ifd'];print(render_nodes)"
        """
