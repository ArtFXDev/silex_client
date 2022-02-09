from __future__ import annotations

import logging
import pathlib
import typing
import os
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils import frames
from silex_client.utils import command_builder
from silex_client.utils.parameter_types import MultipleSelectParameterMeta, PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class KickCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "ass_file": {
            "label": "Select Asss",
            "type": PathParameterMeta(extensions=[".ass"]),
            "value": None,
        },
        "frame_range": {
            "label": "Frame range (start, end, step)",
            "type": fileseq.FrameSet,
            "value": "1-50x1",
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "render_layers": {
            "label": "Select render layers",
            "type": MultipleSelectParameterMeta(),
        },
        "output_path": {"type": pathlib.Path, "value": "", "hide": True},
    }
    
    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        if parameters['ass_file'] is not None:
            
            # Get render layers when a ass_file is selected
            render_layers: List[str] = os.listdir(pathlib.Path(parameters['ass_file']).parents[1])

            self.command_buffer.parameters[
                "render_layers"
            ].rebuild_type(*render_layers)


            # Update frame range 
            ass_file = pathlib.Path(parameters['ass_file'])

            path_without_extension: pathlib.Path = ass_file.parents[0] / ass_file.stem
            sequence = fileseq.findSequenceOnDisk( path_without_extension.with_suffix(f".@{ass_file.suffix}"))

            self.command_buffer.parameters['frame_range'].value = sequence.frameSet()

    def _create_render_layer_task(self, general_output_path: pathlib.Path, frame_range: fileseq.FrameSet, task_size: int, ass_file: pathlib.Path, layer: str):
        """Build command for every task (depending on a task size), store them and return a dict"""

        output_path = general_output_path.parents[0] / layer / general_output_path.stem

        kick_cmd = (
            command_builder.CommandBuilder("python", delimiter=" ")
            .value("\\\\prod.silex.artfx.fr\\rez\\windows\\render_kick_ass.py")
            .value(str(output_path))
            .value(general_output_path.suffix.strip('.'))
            .value(ass_file.parents[0])
            .value(ass_file.suffix.strip('.'))
        )

        kick_cmd.add_rez_package('silex_client')

        # Create layer folder 
        os.makedirs(output_path.parents[0], exist_ok=True)

        # Split frames by task
        frame_chunks = frames.split_frameset(frame_range, task_size)
        commands: Dict[str, command_builder.CommandBuilder] = dict()

        # Create commands
        for chunk in frame_chunks:

            chunk_cmd = kick_cmd.deepcopy()

            # Converting chunk back to a frame set
            task_name = chunk.frameRange()

            chunk_cmd.value(chunk)

            # Add ass sequence to argument list
            commands[task_name] = chunk_cmd
        
        return commands

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Target a ass file in a sequence to be used as pattern
        ass_file: pathlib.Path = parameters["ass_file"]

        output_path: pathlib.Path = parameters["output_path"]
        frame_range: fileseq.FrameSet = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        render_layers: List[str] = parameters["render_layers"]

        render_layers_cmd: Dict[str, Dict[str, command_builder.CommandBuilder]] = {}

        for layer in render_layers:
            
            # Build path to ass_file patern so it can be used when creating ass sequence
            ass_file_layer = ass_file.parents[0].stem
            layer_file = pathlib.Path(str(ass_file).replace(ass_file_layer, layer))

            # Create a task dict for each layer
            render_layers_cmd[f'Render layer: {layer}'] = self._create_render_layer_task(output_path, frame_range, task_size, layer_file, layer)

        # Get scene name from path
        scene_name = (ass_file.stem).strip(ass_file.parents[0].stem)

        return {"commands": render_layers_cmd, "file_name": scene_name}
