from __future__ import annotations
import copy

import logging
import pathlib
from typing import Any, Dict, List, Tuple, Union, TYPE_CHECKING
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.files import sequence_exists
from silex_client.utils.parameter_types import (
    PathParameterMeta,
    SelectParameterMeta,
    TextParameterMeta,
)
from silex_client.utils.enums import ConflictBehaviour

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


async def prompt_override(
    command: CommandBase,
    file_path: Union[pathlib.Path, fileseq.FileSequence],
    action_query: ActionQuery,
) -> Tuple[ConflictBehaviour, fileseq.FileSequence]:
    """
    When files already exists, this prompt is used to display the different available behaviours
    to the user. (See ConflictBehaviour enum to see the possible behaviours)
    """
    if isinstance(file_path, pathlib.Path):
        file_path = fileseq.FileSequence(file_path.as_posix())
    # Prompt the user to get the new path
    response = await command.prompt_user(
        action_query,
        {
            "info": {
                "type": TextParameterMeta("info"),
                "value": "Some paths in:\n{file_path}\nAlready exists",
            },
            "conflict_behaviour": {
                "type": SelectParameterMeta(
                    **{
                        behaviour.name.replace("_", " ").title(): behaviour.value
                        for behaviour in list(ConflictBehaviour)
                    }
                ),
                "label": "Select the behaviour for the following conflict",
            },
            "rename": {
                "type": str,
                "label": "Insert the new name",
                "value": file_path.basename(),
            },
            "repath": {
                "type": str,
                "label": "Insert the new path",
                "value": file_path.dirname(),
            },
        },
    )

    conflict_behaviour = ConflictBehaviour(int(response["conflict_behaviour"]))
    if conflict_behaviour is ConflictBehaviour.RENAME:
        file_path.setDirname(str(response["repath"]))
    if conflict_behaviour is ConflictBehaviour.RENAME:
        file_path.setBasename(str(response["rename"]))

    return conflict_behaviour, file_path


class CheckExistingFiles(CommandBase):
    """
    Check if the given files exists, and propose to the user for his preferred
    behaviour.
    This command does not execute the behaviour, it only return the selected behaviour
    """

    parameters = {
        "file_paths": {
            "label": "File path",
            "type": PathParameterMeta(multiple=True),
            "value": None,
        },
        "prompt_override": {
            "label": "Prompt if the file exists",
            "type": bool,
            "value": False,
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
        prompt: bool = parameters["prompt_override"]

        sequences = fileseq.findSequencesInList(file_paths)
        sequences_rename = copy.copy(sequences)
        exists_all = all(
            sequence_exists(sequence, any_file=False) for sequence in sequences
        )
        exists_any = any(
            sequence_exists(sequence, any_file=True) for sequence in sequences
        )

        # Initialize the output with default values
        output = {
            "exists_all": exists_all,
            "exists_any": exists_any,
            "keep_existing": False,
            "file_paths": file_paths,
            "override": True,
        }

        if not prompt or not exists_any:
            return output

        # We prompt the behaviour by sequence
        for index, sequence in enumerate(sequences):
            if not sequence_exists(sequence):
                continue

            conflict_behaviour = action_query.store.get("file_conflict_behaviour")

            if conflict_behaviour is None:
                while not sequence_exists(sequence, any_file=True):
                    conflict_behaviour, sequence = await prompt_override(
                        self, sequence, action_query
                    )
            if conflict_behaviour in [
                ConflictBehaviour.RENAME,
                ConflictBehaviour.REPATH,
            ]:
                sequences_rename[index] = sequence
            if conflict_behaviour in [
                ConflictBehaviour.ALWAYS_OVERRIDE,
                ConflictBehaviour.ALWAYS_KEEP_EXISTING,
            ]:
                action_query.store["file_conflict_behaviour"] = conflict_behaviour
            if conflict_behaviour in [
                ConflictBehaviour.OVERRIDE,
                ConflictBehaviour.ALWAYS_OVERRIDE,
            ]:
                output["override"] = True
                output["keep_existing"] = False
            if conflict_behaviour in [
                ConflictBehaviour.KEEP_EXISTING,
                ConflictBehaviour.ALWAYS_KEEP_EXISTING,
            ]:
                output["override"] = False
                output["keep_existing"] = True

        # The output file paths must be reconstructed from the sequences
        # because the renaming is made by sequence and not by file.
        # However we need to keep the file paths in the same order
        # and grouping the file path by sequence might have broke the initial order
        for file_index, file_path in enumerate(file_paths):
            for sequence_index, sequence in enumerate(sequences):
                if file_path in sequence:
                    new_file_path_index = [
                        pathlib.Path(str(path)) for path in sequence
                    ].index(file_path)
                    file_paths[file_index] = pathlib.Path(
                        str(sequences_rename[sequence_index][new_file_path_index])
                    )

        return output
