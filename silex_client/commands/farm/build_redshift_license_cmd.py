from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class RedshiftLicenseCommand(CommandBase):
    """
    Construct Redshift license commands
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        redshift_cmd = command_builder.CommandBuilder(
            "python",
            rez_packages=["redshift_license_client"],
            delimiter=None,
        ).param("m", "redshift_license_client.main")

        start = redshift_cmd.deepcopy().value("start")
        stop = redshift_cmd.deepcopy().value("stop")

        return {
            "pre_command": str(start),
            "cleanup_command": str(stop),
        }
