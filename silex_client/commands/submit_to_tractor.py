from __future__ import annotations

import pathlib
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import IntArrayParameterMeta
from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import tractor.api.author as author


class TractorSubmitter(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "cmd_list": {
            "label": "Commands list",
            "type": dict,
            "value": [],
        },
        "service": {
            "label": "Service",
            "type": str,
            "value": "TD_TEST_107",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        author.setEngineClientParam(debug=True)

        cmds: Dict[str] = parameters.get('cmd_list')
        service: str = parameters.get('service')
        
        job = author.Job(title=f"vray render", service=service)

        for cmd in cmds:
            logger.info(f"command --> {cmds.get(cmd)}")
            job.newTask(title=str(cmd), argv = cmds.get(cmd))
        

        jid = job.spool()
        logger.info(job.asTcl)
        logger.info(f"Created job --> {jid}")
