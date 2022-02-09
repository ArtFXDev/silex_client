"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of the InsertAction command
"""
from __future__ import annotations

import logging
import pathlib
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_definition import CommandDefinition
from silex_client.action.command_sockets import CommandSockets
from silex_client.resolve.config import Config
from silex_client.utils.socket_types import ListType, PathType, SelectType, TextType
from silex_client.utils.prompt import prompt
from silex_client.utils.files import find_sequence_from_path

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


# TODO: This mapping should be somewhere else
EXTENSION_TYPES_MAPPING = {
    "mb": "ma",
    "tif": "tiff",
    "jpeg": "jpg",
    "hdri": "hdr",
    "hipnc": "hip",
    "hiplc": "hip",
    "hdanc": "hda",
    "hdalc": "hda",
}


class SelectConform(CommandDefinition):
    """
    When conforming a file, the user can either select manually a conform type
    or just let this command use the file extention.
    """

    inputs = {
        "file_paths": {
            "label": "Insert the file to conform",
            "type": PathType(multiple=True),
            "value": None,
            "tooltip": "Insert the path to the file you want to conform",
        },
        "find_sequence": {
            "label": "Conform the sequence of the selected file",
            "type": bool,
            "value": False,
            "tooltip": """
            Allows you to select only one file to conform the entire sequence
            """,
        },
        "auto_select_type": {
            "label": "Auto select the conform type",
            "type": bool,
            "value": True,
            "tooltip": "Guess the conform type from the extension",
        },
        "conform_type": {
            "label": "Select a conform type",
            "type": SelectType(
                *[publish_action["name"] for publish_action in Config.get().conforms]
            ),
            "value": None,
            "tooltip": "Select a conform type in the list",
        },
    }

    outputs = {
        "files": {
            "label": "File sequences to conform",
            "type": ListType(PathType(multiple=True)),
            "value": None,
        },
        "types": {
            "label": "Conform types",
            "type": ListType(str),
            "value": None,
        },
        "frame_sets": {
            "label": "Frame sets",
            "type": ListType(fileseq.FrameSet),
            "value": None,
        },
        "paddings": {
            "label": "Paddings",
            "type": ListType(int),
            "value": None,
        },
    }

    async def _prompt_new_type(
        self, action_query: ActionQuery, sequence: fileseq.FileSequence
    ) -> str:
        """
        Helper to prompt the user for a new conform type and wait for its response
        """
        select_type = await prompt(
            self.buffer,
            action_query,
            {
                "info": {
                    "type": TextType(color="info"),
                    "name": "info",
                    "label": "Info",
                    "value": f"Could not guess the conform type of {sequence}, " +
                        "please select the type of conform you want",
                },
                "select_type": {
                    "type": SelectType(
                        *[
                            publish_action["name"]
                            for publish_action in Config.get().conforms
                        ]
                    ),
                    "name": "select_type",
                    "label": "Conform type",
                },
            },
        )
        return select_type["select_type"]

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_paths"]
        find_sequence: bool = parameters["find_sequence"]
        conform_type: str = parameters["conform_type"]
        auto_select_type: bool = parameters["auto_select_type"]

        sequences = fileseq.findSequencesInList(file_paths)

        # Handle file sequences
        if find_sequence:
            for index, sequence in enumerate(sequences):
                sequences[index] = find_sequence_from_path(
                    pathlib.Path(str(sequence[0]))
                )

        select_conform: Dict[fileseq.FileSequence, Dict[str, Any]] = {}

        # Guess the conform type from the extension of the given file
        for sequence in sequences:
            if not auto_select_type:
                select_conform[sequence] = {"type": conform_type}
                continue

            handled_conform = [action["name"] for action in Config.get().conforms]
            extension = str(sequence.extension())[1:]
            conform_type = extension.lower()

            # Test if the conform is a handled conform type
            conform_type = EXTENSION_TYPES_MAPPING.get(conform_type, conform_type)
            if conform_type in handled_conform:
                select_conform[sequence] = {"type": conform_type}
                continue

            # Try to guess the conform for mutliple extensions (like .tar.gz)
            for conform_type_split in conform_type.split("."):
                conform_type = EXTENSION_TYPES_MAPPING.get(
                    conform_type_split, conform_type_split
                )
                if conform_type in handled_conform:
                    break
            if conform_type in handled_conform:
                select_conform[sequence] = {"type": conform_type}
                continue

            # Some extensions are just not handled at all, the user can select one manually
            logger.warning("Could not guess the conform type of %s", sequence)
            conform_type = await self._prompt_new_type(action_query, sequence)
            select_conform[sequence] = {"type": conform_type}

        for sequence, data in select_conform.items():
            data["frame_set"] = sequence.frameSet() or fileseq.FrameSet(0)
            data["padding"] = sequence._zfill

        return {
            "files": [
                [pathlib.Path(str(file)) for file in sequence]
                for sequence in select_conform
            ],
            "types": [data["types"] for data in select_conform.values()],
            "frame_sets": [data["frame_set"] for data in select_conform.values()],
            "paddings": [data["padding"] for data in select_conform.values()],
        }

    async def setup(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        parameters.get_buffer("conform_type").hide = parameters.get(
            "auto_select_type", False
        )
