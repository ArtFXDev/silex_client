from __future__ import annotations

import typing
from typing import Any, Dict, List
import os
import logging

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import MultipleSelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError, ContentTypeError, InvalidURL
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
            "type": MultipleSelectParameterMeta(),
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "No Title"
        },
        "projects": {
            "label": "Project",
            "type": MultipleSelectParameterMeta(),
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
            logger.info(f"Creating task: {cmds.get(cmd)}")

            # Create the task
            task = author.Task(title=str(cmd))

            # Create a command that will mount the marvin
            pre_command = author.Command(argv=["net", "use", "\\\\marvin", "/user:etudiant", "artfx2020"])
            task.addCommand(pre_command)
            pre_command = author.Command(argv=["net", "use", "\\\\192.168.2.204", "/user:etudiant", "artfx2020"]) # needed for some pool
            task.addCommand(pre_command)

            # Create the main command
            command = author.Command(argv=cmds.get(cmd))
            task.addCommand(command)
            job.addChild(task)

        # Spool the job
        jid = job.spool(owner=owner)
        logger.info(f"Created job: {jid} (jid)")

    
    async def setup(
        self, parameters: Dict[str, Any], action_query: ActionQuery, logger: logging.Logger
    ):
        # Execute the http requiests
        try:
            async with aiohttp.ClientSession() as session:
                tractor_host = os.getenv("silex_tractor_host", "")
                async with session.get(f"{tractor_host}/Tractor/config?q=get&file=blade.config") as response:
                    tractor_pools = await response.json()
        except (ClientConnectionError, ContentTypeError, InvalidURL):
            logger.warning("Could not query the tractor pool list, the config is unreachable")
            tractor_pools = {"BladeProfiles": []}

        # Build the list of profile names from the config
        PROFILE_IGNORE = [None, "DEV", "Windows10", "Linux64", "Linux32", "Windows8.1", "Windows8", "Windows7", "Windows7_32bit", "WindowsVista64", "WindowsVista32", "WindowsXP", "Windows", "MacOSX"]
        pools = [profile["ProfileName"] for profile in tractor_pools["BladeProfiles"] if profile.get("ProfileName") not in PROFILE_IGNORE]
        self.command_buffer.parameters["pools"].type = MultipleSelectParameterMeta(*pools)
        self.command_buffer.parameters["pools"].value = self.command_buffer.parameters["pools"].type.get_default()


        # Get the list of available projects
        if "project" in action_query.context_metadata:
            self.command_buffer.parameters["projects"].value = action_query.context_metadata["project"]
            self.command_buffer.parameters["projects"].hide = True
        else:
            # If there is no project in the current context return a hard coded list of project for 4th years
            self.command_buffer.parameters["projects"].type = MultipleSelectParameterMeta("WS_Environment", "WS_Lighting")

        self.command_buffer.parameters["projects"].value = self.command_buffer.parameters["projects"].type.get_default()

