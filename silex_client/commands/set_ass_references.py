from __future__ import annotations

import logging
import typing
import pathlib
from arnold import *
from typing import List
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils import files, constants
from silex_client.utils.parameter_types import ListParameterMeta, PathParameterMeta, AnyParameter
import silex_maya.utils.thread as thread_maya


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetAssReferences(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "references": {
            "type":ListParameterMeta(
                AnyParameter
            )
        },
        "node_names": {
            "type": ListParameterMeta(
                str
            )
        },
        "ass_file": {
            "type": PathParameterMeta(extensions=['.ass'])
        },
        "new_ass_file": {
            "type": PathParameterMeta(extensions=['.ass'])
        },
    }

    def _set_reference_in_ass(self, new_ass_file: pathlib.Path, ass_file: pathlib.Path, node_names: List[str], references: List[pathlib.Path]):
        """set references path in a list of nodes"""

        # Open ass file
        AiBegin()
        AiMsgSetConsoleFlags(AI_LOG_ALL)
        AiASSLoad(str(ass_file), AI_NODE_ALL)

        node_to_path_dict = dict()

        # Iter through all shading nodes
        iter = AiUniverseGetNodeIterator(AI_NODE_SHADER)

        while not AiNodeIteratorFinished(iter):
            node = AiNodeIteratorGetNext(iter)
            name = AiNodeGetName( node )

            # Only look for a path in a file node
            if name in node_names:
                sequence = fileseq.findSequencesInList(references[node_names.index(name)])[0]
                template = AiNodeGetStr(node, "filename")
                new_path = files.format_sequence_string(sequence, template, constants.ARNOLD_MATCH_SEQUENCE)
                AiNodeSetStr(node, "filename", new_path)

        AiNodeIteratorDestroy(iter)

        # Save to new location
        AiASSWrite(str(new_ass_file), AI_NODE_ALL, False)
        AiEnd()

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        node_names: List[str] = parameters['node_names']
        ass_file: pathlib.Path = parameters['ass_file']
        new_ass_file: pathlib.Path = parameters['new_ass_file']

        # TODO: This should be done in the get_value method of the ParameterBuffer
        references: List[pathlib.Path] = []
        for reference in parameters["references"]:
            reference = reference.get_value(action_query)[0]
            reference = reference.get_value(action_query)
            references.append(reference)
        
        # set references paths
        await thread_maya.execute_in_main_thread(self._set_reference_in_ass, new_ass_file, ass_file, node_names, references)

        return new_ass_file