from __future__ import annotations

import logging
import typing
import pathlib
import os
from arnold import *
from typing import List
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.prompt import UpdateProgress
from silex_client.utils.datatypes import SharedVariable
from silex_client.utils import files, constants
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    PathParameterMeta,
    AnyParameter,
)
import silex_maya.utils.thread as thread_maya


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetAssReferences(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "references": {"type": ListParameterMeta(AnyParameter)},
        "node_names": {"type": ListParameterMeta(str)},
        "ass_files": {"type": ListParameterMeta(pathlib.Path)},
        "new_ass_files": {"type": ListParameterMeta(pathlib.Path)},
        "is_asset": {"type": bool, 'value': False},
    }

    def _set_reference_in_ass(self, progress, new_ass_files: List[pathlib.Path], ass_files: List[pathlib.Path], node_names: List[str], references: List[pathlib.Path]):
        """set references path for a list of nodes then save in a new location"""

        for index, ass in enumerate(ass_files):
            
            # Update progress bar
            progress.value = index + 1

            # Open ass files
            AiBegin()
            AiMsgSetConsoleFlags(AI_LOG_ALL)

            AiASSLoad(str(ass), AI_NODE_ALL)

            # Iter through all shading nodes
            iter = AiUniverseGetNodeIterator(AI_NODE_ALL)

            while not AiNodeIteratorFinished(iter):
                node = AiNodeIteratorGetNext(iter)
                name = AiNodeGetName(node)

                if name in node_names:
                    sequence = fileseq.findSequencesInList(
                        references[node_names.index(name)]
                    )[0]

                    template = AiNodeGetStr(node, "filename")

                    new_path = files.format_sequence_string(
                        sequence, template, constants.ARNOLD_MATCH_SEQUENCE
                    )

                    AiNodeSetStr(node, "filename", new_path)

            AiNodeIteratorDestroy(iter)

            # corresponding new path
            new_path = new_ass_files[ass_files.index(ass)]

            # Save .ass file to new location
            os.makedirs(new_path.parents[0], exist_ok=True)
            AiASSWrite(str(new_path), AI_NODE_ALL, False)
            AiEnd()

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        node_names: List[str] = parameters["node_names"]
        ass_files: List[pathlib.Path] = parameters["ass_files"]
        new_ass_files: List[pathlib.Path] = parameters["new_ass_files"]
        is_asset: bool = parameters["is_asset"]

        # TODO: This should be done in the get_value method of the ParameterBuffer
        references: List[pathlib.Path] = []
        for reference in parameters["references"]:
            reference = reference.get_value(action_query)[0]
            reference = reference.get_value(action_query)
            references.append(reference)
        
        if not is_asset:
            def add_asset_folder(ass):
                """Add asset folder """
                directory = ass.parents[0]
                file_name = str(ass).split('\\')[-1]
                extension = ass.suffix
                return directory / 'assets' / file_name

            # Format paths (add asset folder)
            new_ass_files = list(map(add_asset_folder, new_ass_files))
        
        # set references paths and display progress bar
        progress = SharedVariable(0)

        async with UpdateProgress(
            self.command_buffer,
            action_query,
            progress,
            SharedVariable(len(ass_files)),
            0.2,
        ):
            await thread_maya.execute_in_main_thread(self._set_reference_in_ass, progress, new_ass_files, ass_files, node_names, references)

        return {"new_ass_files": new_ass_files}
