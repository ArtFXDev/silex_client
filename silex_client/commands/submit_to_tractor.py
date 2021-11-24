from __future__ import annotations

import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import MultipleSelectParameterMeta, SelectParameterMeta

import logging

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
            "type": MultipleSelectParameterMeta(*["G_212", "G_201", "TD_TEST_107"]),
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "No Title"
        },
        # "projects": {
        #     "label": "Project",
        #     "type": MultipleSelectParameterMeta(*["WS_Environment", "WS_Lighting"]),
        # },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):

        author.setEngineClientParam(debug=True)

        cmds: Dict[str, str] = parameters['cmd_list']
        pools: List[str] = parameters['pools']
        # projects: List[str] = parameters['projects']
        projects: List[str] = [action_query.context_metadata.get("project")]
        job_title: str = parameters['job_title']

        # Get owner from context
        owner: str = action_query.context_metadata.get("user_email")

        # Check if 4rth year render
        if owner is None:
            owner = "3D4"
            response: Dict[Any] =  await self.prompt_user(action_query, {"project":ParameterBuffer(name = "project", type = SelectParameterMeta(*["WS_Environment", "WS_Lighting"]), label = "Project", value = "WS_Environment")})
            projects = [response.get("project")]


        # Set service
        if len(pools) == 1:
            services = pools[0]
        else:
            services = "(" + " || ".join(pools) + ")"

        logger.info(f"Rendering on pools: {services}")

        job = author.Job(
            title=f"render - {job_title}", projects=projects, service=services)

        
        # Create job
        for cmd in cmds:
            logger.info(f"command: {cmds.get(cmd)}")
            pre_cmd = author.Task(title="Mount marvin", argv=[
                "net", "use", "\\\\marvin", "/user:etudiant", "artfx2020"])

            task = author.Task(title=str(cmd), argv=cmds.get(cmd))
            task.addChild(pre_cmd)

            job.addChild(task)


        jid = job.spool(owner=owner)
        logger.info(f"Created job: {jid} (jid)")
