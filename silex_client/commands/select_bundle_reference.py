from __future__ import annotations

import copy
import logging
import pathlib
import typing
import os
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.resolve.config import Config
from silex_client.utils.parameter_types import PathParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectBundleReference(CommandBase):
    """
    Handles assignement of a new bundle type (references only) e and wait for its response
    """

    parameters = {
        "file_paths": {
            "label": "insert file to bundle",
            "type": PathParameterMeta(multiple=True),
            "hide": True
        },
         "find_sequence": {
            "label": "Conform the sequence of the selected file",
            "type": bool,
            "value": False,
            "tooltip": "The file sequences will be automaticaly detected from the file you select",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_paths"]
        find_sequence: bool = parameters["find_sequence"]
        
        sequences = fileseq.findSequencesInList(file_paths)
        conform_types = []
        frame_sets = [
            sequence.frameSet() or fileseq.FrameSet(0) for sequence in sequences
        ]
        paddings = [sequence._zfill for sequence in sequences]

        # Guess the conform type from the extension of the given file
        for sequence in sequences:
            
            # Guess the conform type from the extension of the given file
            handled_conform = [
                publish_action["name"] for publish_action in Config.get().conforms
            ]
            extension = str(sequence.extension())[1:]
            conform_type = extension.lower()

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

            # Test if the conform is a handled conform type
            conform_type = EXTENSION_TYPES_MAPPING.get(conform_type, conform_type)
            if conform_type in handled_conform:
                conform_types.append(conform_type)
                continue

            # Try to guess the conform for mutliple extensions (like .tar.gz)
            for conform_type_split in conform_type.split("."):
                conform_type = EXTENSION_TYPES_MAPPING.get(
                    conform_type_split, conform_type_split
                )
                if conform_type in handled_conform:
                    break
            if conform_type in handled_conform:
                conform_types.append(conform_type)
                continue

            conform_type = 'default'
            conform_types.append(conform_type)

        # Convert the fileseq's sequences into list of pathlib.Path
        sequences_copy = copy.deepcopy(sequences)
        sequences = []
        for sequence in sequences_copy:
            # For sequences of one item, don't return a list
            if len(sequence) > 1:
                sequences.append([pathlib.Path(str(path)) for path in list(sequence)])
                continue

            sequences.append(pathlib.Path(str(sequence[0])))

        # Simply return what was sent if find_sequence not set
        if find_sequence:
            # Handle file sequences
            for index, sequence in enumerate(sequences):
                if not sequence:
                    continue
                file_path = sequence if not isinstance(sequence, list) else sequence[0]
                for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
                    # Find the file sequence that correspond the to file we are looking for
                    sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
                    if file_path in sequence_list and len(sequence_list) > 1:
                        frame_sets[index] = file_sequence.frameSet()
                        sequences[index] = sequence_list
                        paddings[index] = file_sequence._zfill
                        break

            # Finding sequences might result in duplicates
            sequences_copy = copy.deepcopy(sequences)
            for index, sequence in enumerate(sequences_copy):
                offset = len(sequences_copy) - len(sequences)
                if sequence in sequences[: index - offset]:
                    sequences.pop(index - offset)
                    frame_sets.pop(index - offset)
                    paddings.pop(index - offset)
                    conform_types.pop(index - offset)
        
        return {
            "files": [
                {"file_paths": sequence, "frame_set": frame_set, "padding": padding, 'is_reference': True}
                for sequence, frame_set, padding in zip(sequences, frame_sets, paddings)
            ],
            "types": conform_types,
        }
