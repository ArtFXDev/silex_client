from __future__ import annotations

import os
import pathlib
import typing
from typing import Any, Dict

import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.resolve.config import Config

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectConform(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "file_path": {
            "label": "Insert the file to conform",
            "type": pathlib.Path,
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
                *[publish_action["name"] for publish_action in Config().conforms]
            ),
            "value": None,
            "tooltip": "Select a conform type in the list",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        file_path: pathlib.Path = parameters["file_path"]
        find_sequence: bool = parameters["find_sequence"]
        conform_type: str = parameters["conform_type"]
        auto_select_type: bool = parameters["auto_select_type"]

        # Guess the conform type from the extension of the given file
        if auto_select_type:
            extension = file_path.suffix[1:]
            conform_type = extension.lower()
            # Some extensions are not the exact same as their conform type
            if conform_type not in [
                publish_action["name"] for publish_action in Config().conforms
            ]:
                # TODO: This mapping should be somewhere else
                EXTENSION_TYPES_MAPPING = {
                    "mb": "ma",
                    "jpeg": "jpg",
                    "hdri": "hdr",
                    "hipnc": "hip",
                    "hiplc": "hip",
                }
                # Find the right conform action for the given extension
                conform_type = EXTENSION_TYPES_MAPPING.get(conform_type)

            # Some extensions are just not handled at all
            if conform_type is None:
                raise Exception(
                    "Could not guess the conform for the selected file: The extension %s does not match any conform",
                    extension,
                )

        frame_set = fileseq.FrameSet(0)
        file_paths = [file_path]
        if not find_sequence:
            return {"type": conform_type, "file_paths": file_paths, "frame_set": frame_set}

        for file_sequence in fileseq.findSequencesOnDisk(str(file_path.parent)):
            # Find the file sequence that correspond the to file we are looking for
            sequence_list = [pathlib.Path(str(file)) for file in file_sequence]
            if file_path in sequence_list and len(sequence_list) > 1:
                frame_set = file_sequence.frameSet()
                file_paths = sequence_list
                break

        return {"type": conform_type, "file_paths": file_paths, "frame_set": frame_set}
