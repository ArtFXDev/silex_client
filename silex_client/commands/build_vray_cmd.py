from __future__ import annotations

import pathlib
import typing
import os
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class VrayCommand(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "scene_file": {
            "label": "Scene file",
            "type": pathlib.Path
        },
        "frame_range": {
            "label": "Frame range (stat, end, pad)",
            "type": IntArrayParameterMeta(3),
            "value": [0, 100, 1]
        },
        "task_size": {
            "label": "Task size",
            "type": int,
            "value": 10,
        },
        "skip_existing": {
            "label": "Skip existing frames",
            "type": bool,
            "value": True
        },
         "export_dir": {
            "label": "File directory",
            "type": str,
            "value": "",
        },
         "exoprt_name": {
            "label": "File name",
            "type": pathlib.Path,
            "value": "",
        },
         "extension": {
            "label": "File extension",
            "type": str,
            "value": None,
        },
    }

    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def _list_from_padding(self, lst: List[str], pad: int) -> List[str]:

        return [i for i in range(0, len(lst), pad)]

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        directory: str = parameters.get("export_dir")
        exoprt_name: str = str(parameters.get("exoprt_name"))
        extension: str = parameters.get("extension")
        scene: pathlib.Path = parameters['scene_file']
        frame_range: List[int] = parameters["frame_range"]
        task_size: int = parameters["task_size"]
        skip_existing: int =  int(parameters["skip_existing"])
        
        ### TEMP ###
        ##############
        if directory is not None:
            directory = directory.replace( "D:", r"\\marvin\TEMP_5RN" )
        ##############
    
            export_file: pathlib.Path = os.path.join(directory,f"{exoprt_name}.{extension}")


        arg_list = [
            # V-Ray exe path
            "C:/Maya2022/Maya2022/vray/bin/vray.exe",

            # Don't show VFB (render view)
            "-display=0",

            # Update frequency for logs
            "-progressUpdateFreq=2000",

            # Don't format logs with colors
            "-progressUseColor=0",

            # Use proper carrier returns
            "-progressUseCR=0",

            # Specify the scene file
            f"-sceneFile={scene}",

            # Render already existing frames or not
            f"-skipExistingFrames={skip_existing}",

            # "-rtEngine=5", # CUDA or CPU?
        ]

        # Check if context
        if action_query.context_metadata.get("user_email") is not None:
           arg_list.append(f"-imgFile={export_file}")

        # Create frame_lists with pading
        frame_chunks: List[Any] = list(self._list_from_padding(
            list(range(frame_range[0], frame_range[1] + 1)),  frame_range[2]))

        # Cut frames by task
        task_chunks = list(self._chunks(
            frame_chunks, task_size))
        cmd_dict = dict()


        for chunk in task_chunks:
            start, end = chunk[0], chunk[-1]
            frames: str = ";".join(map(str, chunk))
            logger.info(f"Creating a new task with frames: {start} {end}")
            cmd_dict[f"frames={start}-{end} (pading:{frame_range[2]})"] = arg_list + \
                [f"-frames=\"{frames}\""]

        return {
            "commands": cmd_dict,
            "file_name": scene.stem
        }
