from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.commands.build_output_path import BuildOutputPath

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class BuildOutputPathConform(BuildOutputPath):
    """
    BuildOutputPath with extra features to auto complete the parameters
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        return super().__call_(parameters, action_query, logger)
