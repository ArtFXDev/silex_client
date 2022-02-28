from __future__ import annotations

import logging
import typing
from distutils import command
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class RedshiftLicenseCommands(CommandBase):
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

        return {
            "precommands": [redshift_cmd.deepcopy().value("start")],
            "task_cleanup_cmd": redshift_cmd.deepcopy().value("stop"),
        }
