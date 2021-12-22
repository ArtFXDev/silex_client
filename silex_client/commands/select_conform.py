from __future__ import annotations

import pathlib
import copy
import typing
from typing import Any, Dict, List

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import (
    SelectParameterMeta,
    PathParameterMeta,
)
from silex_client.resolve.config import Config
import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectConform(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "file_paths": {
            "label": "Insert the file to conform",
            "type": PathParameterMeta(multiple=True),
            "value": None,
            "tooltip": "Insert the path to the file you want to conform",
        },
        "find_sequence": {
            "label": "Conform the sequence of the selected file",
            "type": bool,
            "value": False,
            "tooltip": "The file sequences will be automaticaly detected from the file you select",
        },
        "auto_select_type": {
            "label": "Auto select the conform type",
            "type": bool,
            "value": True,
            "tooltip": "Guess the conform type from the extension",
        },
        "conform_type": {
            "label": "Select a conform type",
            "type": SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config.get().conforms]
            ),
            "value": None,
            "tooltip": "Select a conform type in the list",
        },
    }

    async def _prompt_new_type(self, action_query: ActionQuery) -> str:
        """
        Helper to prompt the user for a new conform type and wait for its response
        """
        # Create a new parameter to prompt for the new file path
        new_parameter = ParameterBuffer(
            type=SelectParameterMeta(
                *[publish_action["name"] for publish_action in Config.get().conforms]
            ),
            name="new_type",
            label=f"Conform type",
        )
        # Prompt the user to get the new path
        new_type = await self.prompt_user(
            action_query,
            {"new_type": new_parameter},
        )
        return new_type["new_type"]

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        file_paths: List[pathlib.Path] = parameters["file_paths"]
        find_sequence: bool = parameters["find_sequence"]
        conform_type: str = parameters["conform_type"]
        auto_select_type: bool = parameters["auto_select_type"]

        sequences = fileseq.findSequencesInList(file_paths)
        conform_types = []
        frame_sets = [
            sequence.frameSet() or fileseq.FrameSet(0) for sequence in sequences
        ]
        paddings = [len(sequence.padding()) for sequence in sequences]

        # Guess the conform type from the extension of the given file
        for sequence in sequences:
            if not auto_select_type:
                conform_types.append(conform_type)
                continue

            extension = str(sequence.extension())[1:]
            conform_type = extension.lower()
            # Some extensions are not the exact same as their conform type
            if conform_type not in [
                publish_action["name"] for publish_action in Config.get().conforms
            ]:
                # TODO: This mapping should be somewhere else
                EXTENSION_TYPES_MAPPING = {
                    "bgeo.sc": "bgeo",
                    "mb": "ma",
                    "tif": "tiff",
                    "jpeg": "jpg",
                    "hdri": "hdr",
                    "hipnc": "hip",
                    "hiplc": "hip",
                    "hdanc": "hda",
                    "hdalc": "hda",
                }
                # Find the right conform action for the given extension
                conform_type = EXTENSION_TYPES_MAPPING.get(conform_type, "")

            # Some extensions are just not handled at all
            if conform_type not in [
                publish_action["name"] for publish_action in Config.get().conforms
            ]:
                logger.warning("Could not guess the conform type of %s", sequence)
                conform_type = await self._prompt_new_type(action_query)

            conform_types.append(conform_type)

        # Convert the fileseq's sequences into list of pathlib.Path
        sequences_copy = copy.deepcopy(sequences)
        sequences = []
        for sequence in sequences_copy:
            # For sequences of one item, don't return a list
            if len(sequence) > 1:
                sequences.append([pathlib.Path(str(path)) for path in list(sequence)])
                continue
            elif len(sequence) == 1:
                sequences.append(pathlib.Path(str(sequence[0])))

        # Simply return what was sent if find_sequence not set
        if not find_sequence:
            return {
                "files": [
                    {"file_paths": sequence, "frame_set": frame_set, "padding": padding}
                    for sequence, frame_set, padding in zip(
                        sequences, frame_sets, paddings
                    )
                ],
                "types": conform_types,
            }

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
                    paddings[index] = len(file_sequence.padding())
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
                {"file_paths": sequence, "frame_set": frame_set, "padding": padding}
                for sequence, frame_set, padding in zip(sequences, frame_sets, paddings)
            ],
            "types": conform_types,
        }

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if parameters.get("auto_select_type", False):
            self.command_buffer.parameters["conform_type"].hide = True
        else:
            self.command_buffer.parameters["conform_type"].hide = False
