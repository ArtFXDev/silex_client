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


class TractorSubmiter(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "cmd_list": {
            "label": "Commands list",
            "type": dict,
            "value": [],
        },
        "pools": {
            "label": "Pool",
            "type": MultipleSelectParameterMeta(*["G_212", "TD_TEST_107"]),
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

        cmds: Dict[str, str] = parameters['cmd_list']
        pools: List[str] = parameters['pools']

        owner: str = parameters['owner']
        projects: List[str] = parameters['projects']
        job_title: str = parameters['job_title']

        if len(pools) == 1:
            services = pools[0]
        else:
            services = "(" + " || ".join(pools) + ")"

        logger.info(f"Rendering on pools: {services}")

        job = author.Job(
            title=f"render - {job_title}", projects=projects, service=services)

        for cmd in cmds:
            logger.info(f"command: {cmds.get(cmd)}")
            pre_cmd = author.Task(title="Mount marvin", argv=[
                "net", "use", "\\\\marvin", "/user:etudiant", "artfx2020"])

            task = author.Task(title=str(cmd), argv=cmds.get(cmd))
            task.addChild(pre_cmd)

            job.addChild(task)

        jid = job.spool(owner=owner)
        logger.info(f"Created job: {jid} (jid)")
