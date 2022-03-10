from __future__ import annotations

import logging
import typing
import pathlib
from arnold import *
from typing import Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import ListParameterMeta
from silex_client.utils import files, constants

import silex_maya.utils.thread as thread_maya


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GetAssReferences(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "ass_files": {"type": ListParameterMeta(pathlib.Path), "value": []},
    }

    def _get_references_in_ass(self, logger, ass_file: pathlib.Path) -> Dict[str, pathlib.Path]:
        """Parse an .ass file for references then return a dictionary : dict(node_name: reference_path)"""

        # Open ass file
        AiBegin()
        AiMsgSetConsoleFlags(AI_LOG_ALL)
        AiASSLoad(str(ass_file), AI_NODE_ALL)

        node_to_path_dict = dict()

        # Iter through all shading nodes
        iter = AiUniverseGetNodeIterator(AI_NODE_ALL)

        while not AiNodeIteratorFinished(iter):
            node = AiNodeIteratorGetNext(iter)
            node_name = AiNodeGetName(node)

            if AiNodeIs(node, 'image'):
                # Look for textures (images)
                node_to_path_dict[node_name] = pathlib.Path(AiNodeGetStr( node, "filename" ))
                logger.error(f'image: {node_name} -> {node_to_path_dict[node_name]}')
          
            elif AiNodeIs(node, 'procedural'):
                # Look for procedurals (can be ass references,...)
                node_to_path_dict[node_name] = pathlib.Path(AiNodeGetStr( node, "filename" ))
                logger.error(f'procedural: {node_name} -> {node_to_path_dict[node_name]}')

            elif AiNodeIs(node, 'volume'):
                # Look for procedurals (can be ass references,...)
                node_to_path_dict[node_name] = pathlib.Path(AiNodeGetStr( node, "filename" ))
                logger.error(f'volume: {node_name} -> {node_to_path_dict[node_name]}')

            elif AiNodeIs(node, 'photometric_light'):
                # Look for photometric_light
                node_to_path_dict[node_name] = pathlib.Path(AiNodeGetStr( node, "filename" ))
                logger.error(f'photometric_light: {node_name} -> {node_to_path_dict[node_name]}')

        AiNodeIteratorDestroy(iter)
        AiEnd()

        return node_to_path_dict

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        ass_files: List[pathlib.Path] = parameters["ass_files"]

        # Get texture paths in the .ass file
        node_to_path_dict: Dict[
            str, pathlib.Path
        ] = await thread_maya.execute_in_main_thread(
            self._get_references_in_ass, logger,  ass_files[0]
        )

        # Create tow lits with corresponding indexes
        node_names = list(node_to_path_dict.keys())

        references: List[List[pathlib.Path]] = list()

        for item in list(node_to_path_dict.values()):
            logger.error(item)
            temp_list = []
        
            # Add sequence to the references list
            if files.expand_template_to_sequence(item, constants.ARNOLD_MATCH_SEQUENCE):

                for path in files.expand_template_to_sequence(item, constants.ARNOLD_MATCH_SEQUENCE):

                    # Check if path already conformed
                    if not files.is_valid_pipeline_path(pathlib.Path(path)):
                        temp_list.append(pathlib.Path(path))

                references.append(temp_list)

            else:
                # Add, non-sequence paths to the references list
                if not files.is_valid_pipeline_path(pathlib.Path(item)):
                    references.append([item])

        logger.error(references)

        return {
            "node_names": node_names,
            "references": references,
        }
