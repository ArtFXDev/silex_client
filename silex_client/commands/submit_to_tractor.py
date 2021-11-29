from __future__ import annotations

import typing
from typing import Any, Dict, List
import os
import aiohttp
import asyncio
from aiohttp.client_exceptions import ClientConnectionError, ContentTypeError, InvalidURL

from silex_client.core.context import Context
from silex_client.action.command_base import CommandBase
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.utils.parameter_types import MultipleSelectParameterMeta, SelectParameterMeta
from silex_client.utils.log import logger

import logging

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import tractor.api.author as author

def get_pools() -> list[str]:
    """
    Get the pools from the tractor configuration
    """
    async def query_tractor_pools():
        async with aiohttp.clientsession() as session:
            tractor_host = os.getenv("silex_tractor_host", "")
            async with session.get(f"{tractor_host}/tractor/config?q=get&file=blade.config") as response:
                return await response.json()

    # Execute the http requiests
    try:
        tractor_pools = asyncio.run(query_tractor_pools())
    except (ClientConnectionError, ContentTypeError, InvalidURL):
        logger.warning("Could not query the tractor pool list, the config is unreachable")
        return []

    # Build the list of profile names from the config
    profile_ignore = [None, "DEV", "Windows10", "Linux64", "Linux32"]
    return [profile["profilename"] for profile in tractor_pools["bladeprofiles"] if profile.get("profilename") not in profile_ignore]

def get_projects() -> list[str]:
    """
    Get the list of available projects
    """
    if "project" in Context.get().metadata:
        return [Context.get().metadata["project"]]
    
    # If there is no project in the current context
    # Return a hard coded list of project for 4th years
    return ["WS_Environment", "WS_Lighting"]
    

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
            "type": MultipleSelectParameterMeta(*get_pools()),
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "No Title"
        },
        "projects": {
            "label": "Project",
            "type": MultipleSelectParameterMeta(*get_projects()),
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        # Initialize the tractor agent
        author.setEngineClientParam(debug=True)

        cmds: Dict[str, str] = parameters['cmd_list']
        pools: List[str] = parameters['pools']
        projects: List[str] = parameters['projects']
        job_title: str = parameters['job_title']

        # Get owner from context
        owner: str = action_query.context_metadata.get("user_email", "3d4")

        # Set service
        if len(pools) == 1:
            services = pools[0]
        else:
            services = "(" + " || ".join(pools) + ")"
        logger.info(f"Rendering on pools: {services}")

        # Creating the job
        job = author.Job(
            title=job_title, projects=projects, service=services)
        
        # Create the commands
        for cmd in cmds:
            logger.info(f"Command: {cmds.get(cmd)}")

            # Create the task
            task = author.Task(title=str(cmd))

            # Create a command that will mount the marvin
            pre_command = author.Command(argv=["net", "use", "\\\\marvin", "/user:etudiant", "artfx2020"])
            task.addCommand(pre_command)

            # Create the main command
            command = author.Command(argv=cmds.get(cmd))
            task.addCommand(command)
            job.addChild(task)


        # Spool the job
        jid = job.spool(owner=owner)
        logger.info(f"Created job: {jid} (jid)")
