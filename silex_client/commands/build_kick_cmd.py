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
            "type": MultipleSelectParameterMeta(*['masterLayer']),
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
            self.command_buffer.parameters['frame_range'].value = self._find_sequence(ass_file).frameSet()


    def _find_sequence(
        self, file_path: pathlib.Path, frame_range: fileseq.FrameSet = None
    ) -> fileseq.FileSequence:
        """
        Return a file sequence for a specific frame range
        """

        path_without_extension: pathlib.Path = file_path.parents[0] / file_path.stem

        # Find existing ass
        sequence = fileseq.findSequenceOnDisk(
            path_without_extension.with_suffix(f".@{file_path.suffix}")
        )

        if frame_range is not None:

            # Create wanted sequence
            search_sequence = fileseq.FileSequence(
                path_without_extension.with_suffix(f".{frame_range}#{file_path.suffix}")
            )

            sequence = set(list(sequence)).intersection(set(list(search_sequence)))


        return sequence

    def _create_render_layer_task(self, general_output_path: pathlib.Path, frame_range: fileseq.FrameSet, task_size: int, ass_file: pathlib.Path, layer: str):
        """Build command for every task (depending on a task size), store them and return a dict"""

        kick_cmd = (
            command_builder.CommandBuilder("powershell.exe", delimiter=" ")
            .param("ExecutionPolicy", "Bypass")
            .param("NoProfile")
            .param("File", "\\\\prod.silex.artfx.fr\\rez\\windows\\render_kick_ass.ps1")
        )

        output_path = (general_output_path.parents[0] / layer / general_output_path.stem).with_suffix(f'{general_output_path.suffix}')
        kick_cmd.param("ExportFile", str(output_path))

        # Create layer folder 
        os.makedirs(output_path.parents[0], exist_ok=True)

        # Split frames by task
        frame_chunks = frames.split_frameset(frame_range, task_size)
        commands: Dict[str, command_builder.CommandBuilder] = dict()

        # Create commands
        for chunk in frame_chunks:

            chunk_cmd = kick_cmd.deepcopy()

            # Get ass sequence  using a specific frame_range
            sequence =  self._find_sequence(
                ass_file, fileseq.FrameSet(chunk)
            )
            ass_files: List[str] = list(sequence)

            # Converting chunk back to a frame set
            task_name = chunk.frameRange()

            chunk_cmd.param("AssFiles", ",".join(ass_files))

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
