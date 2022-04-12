from __future__ import annotations

import logging
import typing
import pathlib
from typing import List, Dict, Any
import fileseq

from silex_client.action.command_base import CommandBase
from silex_client.utils.files import format_sequence_string
from silex_client.utils.constants import VRAY_MATCH_SEQUENCE
from silex_client.utils.thread import execute_in_thread
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    PathParameterMeta,
    AnyParameter,
)

from vray_sdk import vray as vray_sdk

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetVrsceneReferences(CommandBase):
    """
    Retrieve a stored value from the action's global store
    """

    parameters = {
        "vrscene_src": {"type": PathParameterMeta(multiple=True)},
        "vrscene_dst": {"type": PathParameterMeta(multiple=True)},
        "reference_values": {"type": ListParameterMeta(AnyParameter)},
        "plugins_attributes": {"type": ListParameterMeta(str)},
    }

    @staticmethod
    def _set_vrscene_references(
        vrscene_src: pathlib.Path,
        vrscene_dst: pathlib.Path,
        plugins_names: List[str],
        reference_values: List[List[pathlib.Path]],
        logger: logging.Logger,
    ):
        """
        Set references path for a list of nodes then save in a new location
        """

        def dumpMsg(renderer, message, level, instant):
            if level == vray_sdk.LOGLEVEL_ERROR:
                logger.error(message)
            elif level == vray_sdk.LOGLEVEL_WARNING:
                logger.warning(message)
            elif level == vray_sdk.LOGLEVEL_INFO:
                logger.info(message)
            else:
                logger.debug(message)

        with vray_sdk.VRayRenderer() as renderer:
            # renderer.setOnLogMessage(dumpMsg)
            renderer.load(vrscene_src.as_posix())
            for plugin_name, file_paths in zip(plugins_names, reference_values):
                name = ":".join(plugin_name.split(":")[:-1])
                attribute = plugin_name.split(":")[-1]
                plugin = renderer.plugins[name]
                sequence = fileseq.findSequencesInList(file_paths)[0]
                template = plugin.getValueAsString(attribute)

                new_value = format_sequence_string(
                    sequence, template, VRAY_MATCH_SEQUENCE
                )

                plugin.setValueAsString(attribute, new_value)

            logger.info("Exporting vrscene to %s", vrscene_dst)
            renderer.export(vrscene_dst.as_posix())

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        vrscenes_src: List[pathlib.Path] = parameters["vrscene_src"]
        vrscenes_dst: List[pathlib.Path] = parameters["vrscene_dst"]
        plugins_values: List[str] = parameters["plugins_attributes"]

        # TODO: This should be done in the get_value method of the ParameterBuffer
        reference_values: List[List[pathlib.Path]] = []
        for reference in parameters["reference_values"]:
            reference = reference.get_value(action_query)[0]
            reference = reference.get_value(action_query)
            reference_values.append(reference)
        
        # set references paths
        for vrscene_src, vrscene_dst in zip(vrscenes_src, vrscenes_dst):
            await execute_in_thread(
                self._set_vrscene_references,
                vrscene_src,
                vrscene_dst,
                plugins_values,
                reference_values,
                logger,
            )

        return vrscenes_dst
