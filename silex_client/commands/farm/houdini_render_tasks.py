from __future__ import annotations

import json
import logging
import pathlib
import tempfile
import typing
from typing import Any, Dict, List, Union, cast
from silex_client.utils.log import flog

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm, frames
from silex_client.utils.parameter_types import (
    MultipleSelectParameterMeta,
    SelectParameterMeta,
    TaskFileParameterMeta,
    TextParameterMeta,
    IntArrayParameterMeta
)
from silex_client.utils.thread import execute_in_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import subprocess

from silex_client.utils.deadline.job import DeadlineCommandLineJob


class HoudiniRenderTasksCommand(CommandBase):
    """
    Construct Houdini Command
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": TaskFileParameterMeta(extensions=[".hip", ".hipnc"]),
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
        "pre_command": {
            "type": str,
            "hide": True,
            "value": "",
        },
        "cleanup_command": {
            "type": str,
            "hide": True,
            "value": "",
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
        flog.info(rop_nodes)
        output_file = pathlib.Path(parameters["output_filename"])

        if not isinstance(rop_nodes, list):
            rop_nodes = rop_nodes.split(" ")

        ######### BUILD HOUDINI COMMAND

        rop_node = rop_nodes[0]
        rop_name = rop_node.split("/")[-1]

        full_output_file = (
                output_file.parent
                / rop_name
                / f"{output_file.stem}_{rop_name}.$F4{''.join(output_file.suffixes)}"
        )
        flog.info(f"full_output_file : {full_output_file}")
        project = cast(str, action_query.context_metadata["project"]).lower()
        houdini_cmd = (
            command_builder.CommandBuilder(
                "hython",
                rez_packages=[
                    "houdini",
                    project,
                ],
                delimiter=" ",
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

        chunk = FrameSet("1-10")
        incr = "1"

        all_frames = farm.frameset_to_frames_str(chunk)
        houdini_cmd.param("f", all_frames)
        houdini_cmd.param("i", incr)

        '''
        frame_range_str = str(frame_range)
        flog.info(f"frame_range : {frame_range}, {type(frame_range)}")
        frame_range_split = frame_range_str.split("x")
        houdini_cmd.param("i", frame_range_split[-1])
        flog.info(f"i : {frame_range_split[-1]}, {type(frame_range_split[-1])}")
        frame_range_frames = frame_range_split[0].replace("-", " ")
        houdini_cmd.param("f", frame_range_frames)
        flog.info(f"f : {frame_range_frames}, {type(frame_range_frames)}")
        '''


        '''
        for rop_node in rop_nodes:
            rop_name = rop_node.split("/")[-1]

            full_output_file = (
                output_file.parent
                / rop_name
                / f"{output_file.stem}_{rop_name}.$F4{''.join(output_file.suffixes)}"
            )

            # Build the render command
            project = cast(str, action_query.context_metadata["project"]).lower()
            houdini_cmd = (
                command_builder.CommandBuilder(
                    "hython",
                    rez_packages=[
                        "houdini",
                        project,
                    ],
                    delimiter=" ",
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

            rop_task = farm.Task(title=f"ROP node: {rop_name}")
            frame_chunks = frames.split_frameset(frame_range, task_size)

            flog.info(f"frame_chunks : {frame_chunks}")
            # Create tasks for each frame chunk
            for chunk in frame_chunks:
                chunk_cmd = houdini_cmd.deepcopy()
                chunk_cmd.param("f", farm.frameset_to_frames_str(chunk))
                flog.info(f"chunk_cmd 1 : {chunk_cmd}")

                # In case of a more complicated setup add a pre and cleanup command
                if len(parameters["pre_command"]) and len(
                    parameters["cleanup_command"]
                ):
                    mount_cmd = farm.get_mount_command(
                        action_query.context_metadata.get("project_nas")
                    )

                    chunk_cmd = farm.wrap_command(
                        pres=[
                            mount_cmd,
                            farm.Command(argv=parameters["pre_command"].split(" ")),
                            farm.get_clear_frames_command(
                                full_output_file.parent, chunk
                            ),
                        ],
                        cmd=farm.Command(chunk_cmd.as_argv()),
                        post=farm.Command(parameters["cleanup_command"].split(" ")),
                    )
                else:
                    # Wrap the command with the mount drive
                    chunk_cmd = farm.wrap_command(
                        [
                            farm.get_mount_command(
                                action_query.context_metadata["project_nas"]
                            ),
                            farm.get_clear_frames_command(
                                full_output_file.parent, chunk
                            ),
                        ],
                        cmd=farm.Command(chunk_cmd.as_argv()),
                    )

                task = farm.Task(title=str(chunk))
                task.addCommand(chunk_cmd)
                rop_task.addChild(task)

        flog.info(f"chunk_cmd 2 : {chunk_cmd}")
        
        '''

        ###### BUILD DEADLINE JOB

        context = action_query.context_metadata
        user = context["user"].lower().replace(' ', '.')
        cmd = str(houdini_cmd).split(' ', 1)[1]

        flog.info(f"cmd : {cmd}")

        jobs = []

        job = DeadlineCommandLineJob(
            scene.stem,
            user,
            cmd,
            parameters["frame_range"],
            chunk_size=parameters['task_size']
        )

        jobs.append(job)

        return {"jobs": jobs}

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
