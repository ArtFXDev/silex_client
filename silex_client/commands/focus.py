from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import subprocess
import platform


class Focus(CommandBase):
    """
    Dcc on Foreground
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        pid = action_query.context_metadata["pid"]
        if platform.system() == "Windows":
            WINDOW_COMMAND = f"(New-Object -ComObject WScript.Shell).AppActivate((get-process -id {pid}).MainWindowTitle)"
            subprocess.Popen(["Powershell.exe", "-Command", WINDOW_COMMAND], shell=True)
