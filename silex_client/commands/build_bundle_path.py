from __future__ import annotations

import logging
import os
import pathlib
import typing
import uuid
from typing import Any, Dict, Optional
import sys

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils.files import slugify
from silex_client.utils import files

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildBundlePath(CommandBase):
    """
    Build relative path in bundle folder
    """

    parameters = {
        "file_to_bundle": {
            "type": pathlib.Path,
            "hide": True
        },
         "frame_set": {
            "label": "Insert the quantity of items if file sequence",
            "type": fileseq.FrameSet,
            "value": fileseq.FrameSet(0),
            "tooltip": "The range is start, end, increment",
            "hide": True,
        },
        "padding": {
            "label": "padding for index in sequences",
            "type": int,
            "value": 1,
            "hide": True,
        },
        "is_reference": {
            "type": bool,
            "value": 1,
            "hide": True,
        },
        "output_type": {
            "label": "Insert publish type",
            "type": str,
            "value": None,
            "tooltip": "Insert the short name of the output type",
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
    
        file_to_bundle: pathlib.Path = parameters['file_to_bundle']
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        extension: str = parameters["output_type"]
        padding: int = parameters["padding"]
        is_reference: bool = parameters["is_reference"]

        nb_elements = len(frame_set)
        BUNDLE_ROOT = pathlib.Path(os.environ.get('BUNDLE_ROOT'))

        file_name = file_to_bundle.stem
        directory = pathlib.Path(f'$BUNDLE_ROOT') 

        if not files.is_valid_pipeline_path(pathlib.Path(file_to_bundle)):
            # Hashing name: makes sur the hashed value is positive to be intergrated in a path
            file_name = str(hash(file_to_bundle.stem) % ((sys.maxsize + 1) * 2) )

        if is_reference:
            directory = directory / 'references' / file_name
        
        full_name = file_name
        full_names = []
        full_paths = [directory / full_name]

        # Create directoriy using the environement variable
        logger.info(f"Output directory created: {directory}")

        # Handle the sequences of files
        if nb_elements > 1:
            for item in frame_set:
                full_names.append(
                    full_name + f".{str(item).zfill(padding)}.{extension}"
                )
            full_paths = [directory / name for name in full_names]

        else:
            full_names = full_name + f".{extension}"
            full_paths = directory / full_names

        if isinstance(full_paths, list):
            sequence = fileseq.findSequencesInList(full_paths)
            logger.info("Output path(s) built: %s", sequence)
        else:
            logger.info("Output path(s) built: %s", full_paths)
        
        return {
            "directory": directory,
            "file_name": file_name,
            "full_name": full_names,
            "full_path": full_paths,
            "frame_set": frame_set,
        }
