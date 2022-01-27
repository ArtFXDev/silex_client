from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List
from pathlib import Path
from fileseq import FrameSet
from silex_client.utils import frames
from silex_client.action.command_base import CommandBase
from silex_client.utils import command
from silex_client.utils.command import CommandBuilder
from silex_client.utils.frames import split_frameset
from silex_client.utils.parameter_types import IntArrayParameterMeta, PathParameterMeta, SelectParameterMeta
from silex_client.utils.thread import execute_in_thread

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import os
import asyncio
import ast
import subprocess

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
        render_node: str = parameters["render_nodes"]
        output_file: str = parameters["output_filename"]
        output_file = Path(output_file)

        logger.info(output_file)
        output_file = output_file.parent / f"{output_file.with_suffix('').stem}_$F{''.join(output_file.suffixes)}"
        logger.info(output_file)
        logger.info(resolution)

        # Build the mantra command
        houdini_cmd = CommandBuilder("hython", rez_packages=["houdini"], delimiter=" ")
        houdini_cmd.value("C:/Houdini18/bin/hrender.py")
        houdini_cmd.value(str(scene))
        houdini_cmd.param("d", render_node)
        houdini_cmd.param("o", str(output_file))
        houdini_cmd.param("w", resolution[0])
        houdini_cmd.param("h", resolution[1])

        frame_chunks = frames.split_frameset(frame_range, task_size)
        commands: Dict[str, CommandBuilder] = {}

        
        houdini_cmd.param("e")
        # Create commands
        for chunk in frame_chunks:
            task_title = chunk.frameRange()
            # Add the frames argument
            houdini_cmd.param("f", str(chunk).split('-'))
           
            commands[task_title] = houdini_cmd.deepcopy()

        logger.info(commands)
        return {"commands": commands, "file_name": scene.stem}

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        scene: pathlib.Path = parameters["scene_file"]
        previous_hip_value = action_query.store.get("submit_houdini_temp_hip_filepath", None)

        if scene == previous_hip_value:
            return

        if not scene or not os.path.isfile(scene):
            return
        def run(cmd):
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

         
            stdout, stderr = proc.communicate()
            logger.info(f"[{cmd} exited with {proc.returncode}]")
            
            if stdout:
                logger.info(stdout)
                
                stdout = stdout.decode().splitlines()
                for line in stdout :
                    try:
                        logger.info(f"trying to parse stdout: {line}")

                        render_nodes = ast.literal_eval(line)
                        self.command_buffer.parameters["render_nodes"].rebuild_type(*render_nodes)
                        logger.info(f"ok")

                    except Exception as e:
                        logger.info(f"failed to parse stdout: {e}, str: {line}")

            if stderr:
                logger.error(f"stderr: {stderr.decode()}")

        #await run("rez env houdini -- hython -c hou.hipFile.load('D:\mantra_render.hip');render_nodes=hou.node('/out').allSubChildren();print(render_nodes)")
        action_query.store["submit_houdini_temp_hip_filepath"] = scene
        await execute_in_thread(run,f"rez env silex_client-dev houdini -- hython -m silex_client.utils.houdini.get_rop_nodes --file {scene}")