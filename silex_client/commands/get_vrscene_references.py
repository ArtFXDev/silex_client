from __future__ import annotations

from typing import Any, Dict, List
import logging
import typing
import pathlib
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import PathParameterMeta, TextParameterMeta
from silex_client.utils.files import expand_template_to_sequence, is_valid_pipeline_path
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.constants import VRAY_MATCH_SEQUENCE


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from vray_sdk import vray as vray_sdk

# This is the list of plugins to look for in order to find references that
# might be in the vrscene
PLUGIN_MAPPING = {
    "BitmapBuffer": ["file"],
    "GeomMeshFile": ["file"],
    "LightIES": ["ies_file"],
    "PhxShaderCache": ["cache_path"],
}


class GetVrsceneReferences(CommandBase):
    """
    Get all the textures in the given vrscene files
    """

    parameters = {
        "vrscene_files": {"type": PathParameterMeta(multiple=True), "value": []}, "skip_prompt": {'type': bool, 'value': False},
    }

    @staticmethod
    def _get_vrscene_references(file_path: pathlib.Path) -> Dict[str, pathlib.Path]:
        """
        Parse an .vrscene file for textures and return a dictionary : dict(node_name: reference_path)
        """
        plugins_references = {}

        with vray_sdk.VRayRenderer() as renderer:
            renderer.load(file_path.as_posix())
            for plugin in renderer.plugins:
                reference_values = PLUGIN_MAPPING.get(str(plugin.getClass()))
                if reference_values is None:
                    continue
                for reference_value in reference_values:
                    file_path = plugin.getValueAsString(reference_value)
                    if not is_valid_pipeline_path(pathlib.Path(file_path)):
                        plugin_key = f"{plugin.getName()}:{reference_value}"
                        plugins_references[plugin_key] = pathlib.Path(file_path)

        return plugins_references

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        vrscene_files: List[pathlib.Path] = parameters["vrscene_files"]
        skip_prompt: bool = parameters["skip_prompt"]
        
        # Get texture paths in the .vrscene file
        plugins_references: Dict[str, pathlib.Path] = await execute_in_thread(
            self._get_vrscene_references, vrscene_files[0]
        )

        # Create two lists with corresponding indexes
        plugins_names = list(plugins_references.keys())
        references = [
            [
                pathlib.Path(str(path))
                for path in expand_template_to_sequence(item, VRAY_MATCH_SEQUENCE)
            ]
            for item in list(plugins_references.values())
        ]

        # Display a message to the user to inform about all the references to conform
        message = f"The vrscenes\n{fileseq.findSequencesInList(vrscene_files)[0]}\nis referencing non conformed file(s) :\n\n"
        for file_path in plugins_references.values():
            message += f"- {file_path}\n"

        message += "\nThese files must be conformed and repathed first. "
        message += "Press continue to conform and repath them"
        info_parameter = ParameterBuffer(
            type=TextParameterMeta("info"),
            name="info",
            label="Info",
            value=message,
        )
        # Send the message to inform the user
        if references and not skip_prompt:
            await self.prompt_user(action_query, {"info": info_parameter})

        return {
            "plugins": plugins_names,
            "references": references,
        }
