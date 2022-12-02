from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List, cast

from silex_client.action.command_base import CommandBase
from silex_client.utils import farm
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
  
from Deadline.DeadlineConnect import DeadlineCon


class SubmitToDeadlineCommand(CommandBase):
    """
    Send job to Deadline
    """

    parameters = {
        "message": {
            "label": "message",
            "type": str,
        }}

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        deadline = DeadlineCon('localhost', 8081)

        JobInfo = {
            "Name": "CommandLine submit test",
            "UserName": "elise.vidal",
            "Frames": "0-1",
            "Plugin": "CommandLine"

        }

        PluginInfo = {
            "Executable": "C:\\rez\\__install__\\Scripts\\rez\\rez-env.exe",
            "Arguments": f'''testpipe python -- python -c "print('{parameters["message"]}')"'''
        }

        logger.debug("deadline submit script called")

        new_job = deadline.Jobs.SubmitJob(JobInfo, PluginInfo)
