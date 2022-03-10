from __future__ import annotations

import json
import logging
import pathlib
import tempfile
import typing
from typing import Any, Dict, List, Union

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, frames
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    MultipleSelectParameterMeta,
    TaskFileParameterMeta,
    TextParameterMeta,
)
from silex_client.utils.thread import execute_in_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import ast
import os
import subprocess


class HoudiniCommand(CommandBase):
    """
    Construct Houdini Command
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(
                extensions=[".hip", ".hipnc"], use_current_context=True
            ),
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
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": False,
            "hide": True,
        },
        "output_filename": {"type": pathlib.Path, "hide": True, "value": ""},
        "skip_existing": {"label": "Skip existing frames", "type": bool, "value": True},
        "rop_from_hip": {
            "label": "Get ROP node list from scene file",
            "type": bool,
            "value": False,
        },
        "get_rop_progress": {
            "type": TextParameterMeta(
                color="info", progress={"variant": "indeterminate"}
            ),
            "value": "Opening houdini scene...",
            "hide": True,
        },
        "rop_nodes": {
            "label": "ROP node(s) path(s)",
            "type": MultipleSelectParameterMeta(),
            "value": None,
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
        skip_existing = parameters["skip_existing"]
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int] = parameters["resolution"]
        rop_nodes: Union[str, List[str]] = parameters["rop_nodes"]
        output_file = pathlib.Path(parameters["output_filename"])

        node_cmd: Dict[str, Dict[str, command_builder.CommandBuilder]] = {}

        for rop_node in rop_nodes:
            render_name = rop_node.split("/")[-1]

            full_output_file = (
                output_file.parent
                / render_name
                / f"{output_file.with_suffix('').stem}_{render_name}.$F4{''.join(output_file.suffixes)}"
            )

            # Build the render command
            houdini_cmd = (
                command_builder.CommandBuilder(
                    "hython", rez_packages=["houdini"], delimiter=" "
                )
                .param("m", "hrender")
                .value(scene.as_posix())
                .param("d", rop_node)
                .param("o", full_output_file.as_posix())
                .param("v")
                .param("S", condition=skip_existing)
            )

            if parameter_overrides:
                houdini_cmd.param("w", resolution[0])
                houdini_cmd.param("h", resolution[1])

            frame_chunks = frames.split_frameset(frame_range, task_size)
            commands: Dict[str, command_builder.CommandBuilder] = {}

            # Create commands
            for chunk in frame_chunks:
                chunk_cmd = houdini_cmd.deepcopy()
                task_title = chunk.frameRange()

                chunk_cmd.param("f", ";".join(map(str, list(chunk))))

                commands[task_title] = chunk_cmd

            logger.info(f"Commands created: {commands}")

            # Format "commands" output to match the input type in the submiter
            node_cmd[f"ROP node: {rop_node}"] = commands

        return {"commands": node_cmd, "file_name": scene.stem}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        rop_from_hip: bool = parameters["rop_from_hip"]
        previous_hip_value = action_query.store.get(
            "submit_houdini_temp_hip_filepath", None
        )
        hide_overrides = parameters["parameter_overrides"]

        self.command_buffer.parameters["resolution"].hide = not hide_overrides

        if rop_from_hip:
            self.command_buffer.parameters[
                "rop_nodes"
            ].type = MultipleSelectParameterMeta()
        else:
            self.command_buffer.parameters["rop_nodes"].type = str
            return

        if scene == previous_hip_value:
            return

        if not scene or not os.path.isfile(scene):
            return

        self.command_buffer.parameters["get_rop_progress"].hide = False
        await action_query.async_update_websocket()

        tmp_dir = tempfile.mkdtemp()
        tmp_file = os.path.join(tmp_dir, "get_rop_nodes")

        get_rop_cmd = (
            command_builder.CommandBuilder(
                "hython",
                delimiter=None,
                rez_packages=[
                    "houdini",
                    action_query.context_metadata["project"].lower(),
                ],
            )
            .param("m", "get_rop_nodes")
            .param("-hip", scene)
            .param("-tmp", tmp_file)
        )

        def subprocess_rop_node():
            proc = subprocess.Popen(
                get_rop_cmd.as_argv(),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = proc.communicate()
            logger.info(stdout, stderr)

        await execute_in_thread(subprocess_rop_node)

        with open(tmp_file) as f:
            self.command_buffer.parameters["rop_nodes"].rebuild_type(
                *json.loads(f.readlines()[0])
            )

        # Clean tmp dir
        os.remove(tmp_file)
        os.rmdir(tmp_dir)

        self.command_buffer.parameters["get_rop_progress"].hide = True
        action_query.store["submit_houdini_temp_hip_filepath"] = scene
