from __future__ import annotations

import logging
import os
import pathlib
import typing
import uuid
from typing import List
import sys

import fileseq
from silex_client.action.command_base import CommandBase
from silex_client.utils.files import slugify
from silex_client.utils import files
from silex_client.utils.parameter_types import ListParameter


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildBundlePath(CommandBase):
    """
    Build relative path in bundle folder
    """

    parameters = {
        "files_to_bundle": {
            "type": ListParameter,
            "hide": True
        },
         "frame_set": {
            "type": fileseq.FrameSet,
            "value": fileseq.FrameSet(0),
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
    
        files_to_bundle: List[pathlib.Path] = parameters['files_to_bundle']
        frame_set: fileseq.FrameSet = parameters["frame_set"]
        extension: str = parameters["output_type"]
        padding: int = parameters["padding"]
        is_reference: bool = parameters["is_reference"]
        nb_elements = len(files_to_bundle)

        BUNDLE_ROOT = pathlib.Path(os.environ.get('BUNDLE_ROOT'))
        directory = pathlib.Path('${BUNDLE_ROOT}') 

        file_name = files_to_bundle[0].stem

        # get rid of increment if there are multiple elements
        if nb_elements > 1:
            file_name = pathlib.Path(file_name).stem

        if not files.is_valid_pipeline_path(pathlib.Path(files_to_bundle[0])):
            # Hashing name: makes sur the hashed value is positive to be intergrated in a path
            file_name = str(hash(files_to_bundle[0]) % ((sys.maxsize + 1) * 2) )

        if is_reference:
            directory = directory / 'references'
        
        full_name = file_name
        full_names = []
        full_paths = [directory / full_name]

        # Create directory using the environement variable
        os.makedirs( str(directory).replace('${BUNDLE_ROOT}', str(BUNDLE_ROOT)), exist_ok=True)
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
            "full_name": full_names,
            "full_path": full_paths,
        }
