from __future__ import annotations
from concurrent import futures

import pathlib
import typing
from typing import Any, Dict, List
from concurrent.futures import Future

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import MultipleSelectParameterMeta
from silex_client.core.context import Context

from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import tractor.api.author as author
import gazu.project


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
            "label": "Pool",
            "type": str,
            "value": "TD_TEST_107",
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "No Title"
        },
        "owner": {
            "label": "Owner",
            "type": str,
            "value": "3d4",
            "hide": True
        },
        "projects": {
            "label": "Project",
            "type": MultipleSelectParameterMeta(*["WS_Environment", "WS_Lighting"]),
        },
    }


    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        author.setEngineClientParam(debug=True)

        cmds: Dict[str] = parameters.get('cmd_list')
        service: str = parameters.get('service')
        
        owner: str = parameters.get('owner')
        projects: List[str] = parameters.get('projects')
        job_title: str = parameters.get('job_title')
        
        job = author.Job(title=f"vray render - {job_title}", projects=projects, service=service)

        for cmd in cmds:
            logger.info(f"command --> {cmds.get(cmd)}")
            job.newTask(title=str(cmd), argv = cmds.get(cmd))
        

        jid = job.spool(owner=owner)
        logger.info(job.asTcl)
        logger.info(f"Created job --> {jid}")
