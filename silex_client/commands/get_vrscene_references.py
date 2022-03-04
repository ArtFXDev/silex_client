from __future__ import annotations

import logging
import typing
import pathlib
from typing import Dict, List, Any

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import PathParameterMeta
from silex_client.utils.files import expand_template_to_sequence, is_valid_pipeline_path
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.constants import VRAY_MATCH_SEQUENCE


# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import vray

# This is the list of plugins to look for in order to find references that
# might be in the vrscene
PLUGIN_MAPPING = {"BitmapBuffer": ["file"]}


class GetVrsceneReferences(CommandBase):
    """
    Get all the textures in the given vrscene files
    """

    parameters = {
        "vrscene_files": {"type": PathParameterMeta(multiple=True), "value": []},
    }

    @staticmethod
    def _get_vrscene_references(file_path: pathlib.Path) -> Dict[str, pathlib.Path]:
        """
        Parse an .vrscene file for textures and return a dictionary : dict(node_name: reference_path)
        """
        plugins_references = {}

        with vray.VRayRenderer() as renderer:
            renderer.load(file_path)
            for plugin in renderer.plugins:
                reference_values = PLUGIN_MAPPING.get(str(plugin.getClass()))
                if reference_values is None:
                    continue
                for reference_value in reference_values:
                    file_path = plugin.getValueAsString(reference_value)
                    if not is_valid_pipeline_path(file_path):
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
        return {
            "plugins": plugins_names,
            "references": references,
        }
