from __future__ import annotations

import logging
import typing
import pathlib
import os

from silex_client.action.command_base import CommandBase
from silex_client.utils.files import expand_environement_variable
from silex_client.utils.parameter_types import ListParameter

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SetEnv(CommandBase):
    """
    Replace path by environement variables if it exists
    """

    parameters = {
        "paths": {
            "type": ListParameter,
            "value": [''],
            "hide": True,
        },
        "envs": {
            "type":  ListParameter,
            "value": None,
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
        envs: str = parameters['envs']
        paths = parameters['paths']

        for path in paths:
            for env in envs:
                if env and env in os.environ:
                    formated_path =  pathlib.Path(path).as_posix()
                    env_value = pathlib.Path(os.environ.get(env)).as_posix()
                    paths[paths.index(path)] = pathlib.Path(str(formated_path).replace(env_value, f'${env}'))
        
        return {'expanded_paths': paths}
