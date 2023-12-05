from __future__ import annotations

import logging
import typing
import fileseq
import pathlib
from arnold import *
import copy
from typing import Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import ListParameterMeta, TextParameterMeta
from silex_client.utils import files, constants

# import silex_maya.utils.thread as thread_maya
from silex_client.utils.thread import execute_in_thread
from pprint import pprint


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


NODE_TYPES = [
    'image',
    'procedural',
    'volume',
    'photometric_light',
]


class GetAssReferences(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "ass_files": {"type": ListParameterMeta(pathlib.Path), "value": []}, "skip_pipeline_files":{'type': bool, "value": True}, "skip_prompt":{'type': bool, "value": False},
        "task_id":{'type':str, "value":""} 
    }

    def _get_references_in_ass(self, ass_file: pathlib.Path, skip_pipeline_files: bool, task_id: str = "" ) -> Dict[str, pathlib.Path]:
        """Parse an .ass file for references then return a dictionary : dict(node_name: reference_path)"""

        # Open ass file
        AiBegin()
        universe = AiUniverse()
        AiMsgSetConsoleFlags(universe,AI_LOG_ALL)
        AiASSLoad(universe ,str(ass_file), AI_NODE_ALL)

        node_to_path_dict = dict()

        # Iter through all shading nodes
        iter = AiUniverseGetNodeIterator(universe, AI_NODE_ALL)

        while not AiNodeIteratorFinished(iter):
            node = AiNodeIteratorGetNext(iter)
            node_name = AiNodeGetName(node)

            for node_type in NODE_TYPES:
                if AiNodeIs(node, node_type):
                    path = pathlib.Path(AiNodeGetStr( node, "filename" ))
                    # if skip_pipeline_files and files.is_valid_pipeline_path(pathlib.Path(path)): 
                    if skip_pipeline_files and files.is_valid_pipeline_path_ass(pathlib.Path(path),task_id): 
                    
                        continue

                    node_to_path_dict[node_name] = path

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
        skip_pipeline_files: bool = parameters["skip_pipeline_files"]
        skip_prompt: bool = parameters["skip_prompt"]
        task_id: str = parameters["task_id"]

        
        # Get texture paths in the .ass file
        node_to_path_dict: Dict[
            str, pathlib.Path
        ] = await execute_in_thread(
            self._get_references_in_ass, ass_files[0], skip_pipeline_files, task_id
        )


        for node, reference in node_to_path_dict.items():
            temp_list = []
        
            # Add sequence to the references list
            sequence =  files.expand_template_to_sequence(reference, constants.ARNOLD_MATCH_SEQUENCE)

            if sequence:
                for path in sequence:
                    # Check if path already conformed                    
                    temp_list.append(pathlib.Path(path))                    

                node_to_path_dict[node] = temp_list
            else:
                # Add, non-sequence paths to the references list
                node_to_path_dict[node] = [reference]
        
        node_names = list(node_to_path_dict.keys())
        references = list(node_to_path_dict.values())

        # Send the message to inform the user
        if references and not skip_prompt:
            # Display a message to the user to inform about all the references to conform
            message = f"The assfile\n{fileseq.findSequencesInList(ass_files)[0]}\nis referencing non conformed file(s) :\n\n"
            for file_path in references:
                message += f"- {file_path}\n"

            message += "\nThese files must be conformed and repathed first. "
            message += "Press continue to conform and repath them"
            info_parameter = ParameterBuffer(
                type=TextParameterMeta("info"),
                name="info",
                label="Info",
                value=message,
            )

            await self.prompt_user(action_query, {"info": info_parameter})

        return {
            "node_names": node_names,
            "references": references,
        }
