from __future__ import annotations

import logging
import typing
import pathlib

from silex_client.action.command_base import CommandBase
from silex_client.utils.files import expand_environement_variable, find_environement_variable
from silex_client.utils.parameter_types import ListParameter

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class ExpandPaths(CommandBase):
    """
    Expand environement variable if it exists
    """

    parameters = {
        "paths_to_expand": {
            "type": ListParameter,
            "value": [''],
            "hide": True,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        file_paths = parameters['paths_to_expand']

        expanded_paths = list(map(expand_environement_variable,file_paths))
        environement_var = list(set([find_environement_variable(path).group(1) for path in file_paths]  )) 

        return {"expanded_paths": expanded_paths , 'envs': environement_var}