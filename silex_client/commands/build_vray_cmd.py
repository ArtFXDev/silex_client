from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

import gazu.client
import gazu.project
from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, frames
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    RadioSelectParameterMeta,
    TaskFileParameterMeta,
)
from silex_client.utils.tractor import dirmap

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class VrayCommand(CommandBase):
    """
    Construct V-Ray render commands
    """

    parameters = {
        "scene_file": {
            "label": "Scene file (Can select multiple render layers)",
            "type": TaskFileParameterMeta(
                multiple=True, extensions=[".vrscene"], use_current_context=True
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
        },
        "output_path": {"type": pathlib.Path, "hide": True, "value": ""},
        "engine": {
            "label": "RT engine",
            "type": RadioSelectParameterMeta(
                **{"Regular": 0, "CPU RT": 1, "GPU CUDA": 5, "GPU RTX": 7}
            ),
            "value": 0,
        },
        "linux": {
            "label": "Run on Linux",
            "type": bool,
            "value": False,
        },
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

    def _get_layers_from_scenes(
        self, scenes: List[pathlib.Path]
    ) -> Dict[pathlib.Path, str]:
        """Create a conrespondance dict { scene_name: render_layer }"""

        scene_to_layer_dict = dict()

        for scene in scenes:

            layer = scene.stem.split(f"{scene.parents[0].stem}_")[-1]
            scene_to_layer_dict[scene] = layer

        return scene_to_layer_dict

    def _create_render_layer_task(
        self,
        scene: pathlib.Path,
        skip_existing: int,
        output_path: pathlib.Path,
        engine: int,
        parameter_overrides: bool,
        resolution: List[int],
        frame_range: FrameSet,
        task_size: int,
        nas: str,
        linux: bool,
    ):
        """Build command for every task (depending on a task size), store them in a dict and return it"""

        # Build the V-Ray command
        vray_cmd = command_builder.CommandBuilder("vray", rez_packages=["vray"])
        vray_cmd.disable(["display", "progressUseColor", "progressUseCR"])
        vray_cmd.param("progressIncrement", 5)
        vray_cmd.param("verboseLevel", 3)
        vray_cmd.param("rtEngine", engine)
        vray_cmd.param("sceneFile", dirmap(scene.as_posix()))
        vray_cmd.param("skipExistingFrames", skip_existing)
        vray_cmd.param("imgFile", dirmap(output_path.as_posix()))

        # Path mapping for Linux
        if linux:
            vray_cmd.param("remapPath", f"P:=/mnt/{nas}")

        if parameter_overrides:
            vray_cmd.param("imgWidth", resolution[0]).param("imgHeight", resolution[1])

        commands: Dict[str, command_builder.CommandBuilder] = {}

        # Split frames by task size
        frame_chunks = frames.split_frameset(frame_range, task_size)

        # Creating tasks for each frame chunk
        for chunk in frame_chunks:
            chunk_cmd = vray_cmd.deepcopy()
            fmt_frames = ";".join(map(str, list(chunk)))

            task_title = chunk.frameRange()

            chunk_cmd.param("frames", fmt_frames)

            # Add the frames argument
            commands[task_title] = chunk_cmd

        return commands

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        vray_scenes: List[pathlib.Path] = parameters["scene_file"]
        output_path: pathlib.Path = parameters["output_path"]
        engine: int = parameters["engine"]
        frame_range: FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        skip_existing = int(parameters["skip_existing"])
        parameter_overrides: bool = parameters["parameter_overrides"]
        resolution: List[int] = parameters["resolution"]

        project_dict = await gazu.project.get_project_by_name(
            action_query.context_metadata["project"]
        )
        nas = project_dict["data"]["nas"]

        # Match selected vrscenes with their attributed render layers
        scene_to_layer_dict = self._get_layers_from_scenes(vray_scenes)

        render_layers_cmd: Dict[str, Dict[str, command_builder.CommandBuilder]] = dict()

        for scene in vray_scenes:
            layer_name = scene_to_layer_dict[scene]

            # The outputed image goes into a layer folder
            full_output_path = (
                output_path.parents[0]
                / layer_name
                / f"{output_path.stem}{output_path.suffix}"
            )

            # Get tasks for each render layer

            render_layers_cmd[
                f"Render layer: {layer_name}"
            ] = self._create_render_layer_task(
                scene,
                skip_existing,
                full_output_path,
                engine,
                parameter_overrides,
                resolution,
                frame_range,
                task_size,
                nas,
                parameters["linux"],
            )

        # Take the first path job title
        if len(scene_to_layer_dict) != 0:
            first_key = list(scene_to_layer_dict.keys())[0]
            render_layer = scene_to_layer_dict[first_key]
            scene_name = str(first_key.stem).split(render_layer)[0][:-1]
        else:
            # For THE group outside of silex... ( TRAITORS !! REBELS !! hum.. hum...)
            scene_name = vray_scenes[0]

        return {
            "commands": render_layers_cmd,
            "file_name": scene_name,
            "mount": not parameters["linux"],
        }
