from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List
<<<<<<< HEAD
import os
import uuid
=======
>>>>>>> 48d2716 (Reformat files)

import gazu.client
import gazu.project

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (MultipleSelectParameterMeta,
                                                SelectParameterMeta)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import aiohttp
import tractor.api.author as author
from aiohttp.client_exceptions import (ClientConnectionError, ContentTypeError,
                                       InvalidURL)


class TractorSubmiter(CommandBase):
    """
    Send job to tractor
    """

    parameters = {
        "precommands": {
            "label": "Pre-commands list",
            "type": list,
            "value": [],
            "hide": True,
        },
        "cmd_list": {
            "label": "Commands list",
            "type": dict,
        },
        "pools": {
            "label": "Pool",
            "type": MultipleSelectParameterMeta(),
        },
        "job_title": {"label": "Job title", "type": str, "value": "No Title"},
        "project": {
            "label": "Project",
            "type": str,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Initialize the tractor agent
        author.setEngineClientParam(debug=True)

        precommands: List[str] = parameters["precommands"]
        cmds: Dict[str, str] = parameters["cmd_list"]
        pools: List[str] = parameters["pools"]
        project: str = parameters["project"]
        job_title: str = parameters["job_title"]
        owner: str = ""

        # MOUNT SERVER
        if action_query.context_metadata.get("user_email") is not None:
            project_dict = await gazu.project.get_project_by_name(project)
            project_data = project_dict["data"]

            if project_data is None:
                raise Exception("NO PROJECTS FOUND")

            SERVER_ROOT = project_data["nas"]

            precommands: List[str] = [
                [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-NoProfile",
                    "-File",
                    "\\\\prod.silex.artfx.fr\\rez\\windows\\set-rd-drive.ps1",
                    SERVER_ROOT,
                ]
            ]

            # Get owner from context
            owner: str = action_query.context_metadata.get("user_email", None).split(
                "@"
            )[
                0
            ]  # get name only
        else:

            mount: List[str] = [
                [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-NoProfile",
                    "-File",
                    "\\\\prod.silex.artfx.fr\\rez\\windows\\set-rd-drive_3d4.ps1",
                    "marvin",
                ]
            ]

            precommands.extend(mount)

            # Get owner from context
            owner: str = "3d4"

        # Set service
        if len(pools) == 1:
            services = pools[0]
        else:
            services = "(" + " || ".join(pools) + ")"
        logger.info(f"Rendering on pools: {services}")

        # Creating the job
        job = author.Job(
            title=job_title,
            priority=100.0,
            tags=["render"],
            projects=[project],
            service=services,
        )

        # Create the commands
        for cmd in cmds:
            # Create the task
            task = author.Task(title=str(cmd))
            
            # add precommands
            for pre_index, pre in enumerate(precommands):
                params = {"argv":pre, "id":str(uuid.uuid4())}
                
                if pre_index > 0:
                    params["refersto"] = task.cmds[pre_index-1].id
                
                pre_command = author.Command(**params)

                # add precommand
                task.addCommand(pre_command)

            # Create the main command
            params = {"argv":cmds.get(cmd), "id":str(uuid.uuid4())}
            if len(precommands) > 0:
                params["refersto"] = task.cmds[-1].id
            
            command = author.Command(**params)

            # add the main command
            task.addCommand(command)
            job.addChild(task)

        # Spool the job
        jid = job.spool(owner=owner)
        logger.info(f"Created job: {jid} (jid)")

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Execute the http requests
        try:
            async with aiohttp.ClientSession() as session:
                tractor_host = os.getenv("silex_tractor_host", "")
                async with session.get(
                    f"{tractor_host}/Tractor/config?q=get&file=blade.config"
                ) as response:
                    tractor_pools = await response.json()
        except (ClientConnectionError, ContentTypeError, InvalidURL):
            logger.warning(
                "Could not query the tractor pool list, the config is unreachable"
            )
            tractor_pools = {"BladeProfiles": []}

        # Build list of profile names from the config
        PROFILE_IGNORE = [
            None,
            "DEV",
            "Windows10",
            "Linux64",
            "Linux32",
            "Windows8.1",
            "Windows8",
            "Windows7",
            "Windows7_32bit",
            "WindowsVista64",
            "WindowsVista32",
            "WindowsXP",
            "Windows",
            "MacOSX",
        ]
        pools = [
            profile["ProfileName"]
            for profile in tractor_pools["BladeProfiles"]
            if profile.get("ProfileName") not in PROFILE_IGNORE
        ]
        self.command_buffer.parameters["pools"].type = MultipleSelectParameterMeta(
            *pools
        )
        pool_parameter = self.command_buffer.parameters["pools"]
        if pool_parameter.value is None:
            pool_parameter.value = pool_parameter.type.get_default()

        # Get the list of available projects
        if "project" in action_query.context_metadata:
            self.command_buffer.parameters["project"].type = SelectParameterMeta(
                action_query.context_metadata["project"]
            )
            self.command_buffer.parameters["project"].hide = True
        else:
            # If there is no project in the current context return a hard coded list of project for 4th years
            self.command_buffer.parameters["project"].type = SelectParameterMeta(
                "WS_Environment", "WS_Lighting"
            )

        self.command_buffer.parameters[
            "project"
        ].value = self.command_buffer.parameters["project"].type.get_default()
