from __future__ import annotations

import logging
import os
import typing
import uuid
from typing import Any, Dict, List

import gazu.client
import gazu.project
from silex_client.action.command_base import CommandBase
from silex_client.utils.command import CommandBuilder
from silex_client.utils.parameter_types import (
    DictParameterMeta,
    MultipleSelectParameterMeta,
    SelectParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import aiohttp
import tractor.api.author as author
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ContentTypeError,
    InvalidURL,
)


class TractorSubmiter(CommandBase):
    """
    Send job to Tractor
    """

    parameters = {
        "precommands": {
            "label": "Pre-commands list",
            "type": list,
            "value": [],
            "hide": True,
        },
        "commands": {
            "label": "Commands list",
            "type": DictParameterMeta(str, CommandBuilder),
            "hide": True,
        },
        "pools": {
            "label": "Pool",
            "type": MultipleSelectParameterMeta(),
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "untitled",
            "hide": True,
        },
        "project": {
            "label": "Project",
            "type": SelectParameterMeta(),
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        precommands: List[CommandBuilder] = parameters["precommands"]
        commands: Dict[str, CommandBuilder] = parameters["commands"]
        pools: List[str] = parameters["pools"]
        project: str = parameters["project"]
        job_title: str = parameters["job_title"]
        owner = ""

        # This command will mount network drive
        mount_cmd = (
            CommandBuilder("powershell.exe", delimiter=None)
            .param("ExecutionPolicy", "Bypass")
            .param("NoProfile")
        )

        if "project" in action_query.context_metadata:
            project_dict = await gazu.project.get_project_by_name(project)

            if not project_dict:
                Exception(f"Project {project} doesn't exist")

            try:
                project_dict["data"]["nas"]
            except KeyError:
                raise Exception(f"Project {project} doesn't have data or nas key")

            owner = action_query.context_metadata["user_email"].split("@")[0]
            mount_cmd.param(
                "File",
                [
                    "\\\\prod.silex.artfx.fr\\rez\\windows\\set-rd-drive.ps1",
                    project_dict["data"]["nas"],
                ],
            )
        else:
            owner = "3d4"
            mount_cmd.param(
                "File",
                [
                    "\\\\prod.silex.artfx.fr\\rez\\windows\\set-rd-drive_3d4.ps1",
                    "marvin",
                ],
            )

        # Add the mount command
        precommands.append(mount_cmd)

        # Set the services the job will run on (groups of blades)
        if len(pools) == 1:
            services = pools[0]
        else:
            services = "(" + " || ".join(pools) + ")"

        # Create a job
        job = author.Job(
            title=job_title,
            priority=100.0,
            tags=["render"],
            projects=[project],
            service=services,
        )

        # Create the render tasks for each command
        for task_title, task_argv in commands.items():
            # Create task
            task: author.Task = author.Task(title=task_title)

            # Add precommands to each task
            all_commands = precommands + [task_argv]

            last_id = None

            # Add every command to the task
            for index, command in enumerate(all_commands):
                if "project" in action_query.context_metadata:
                    # Add the project in the rez environment
                    command.add_rez_package(
                        action_query.context_metadata["project"].lower()
                    )

                # Generates a random uuid for every command
                id = str(uuid.uuid4())
                params = {"argv": command.as_argv(), "id": id}

                # Every command refers to the previous one
                if index > 0:
                    params["refersto"] = last_id

                task.addCommand(author.Command(**params))
                last_id = id

            # Add the task as child
            job.addChild(task)

        # Submit the job to Tractor
        jid = job.spool(owner=owner)
        logger.info(f"Sent job: {job_title} ({jid})")

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        # Query the Tractor config
        try:
            async with aiohttp.ClientSession() as session:
                tractor_host = os.getenv("silex_tractor_host", "")
                tractor_config_url = (
                    f"{tractor_host}/Tractor/config?q=get&file=blade.config"
                )
                async with session.get(tractor_config_url) as response:
                    tractor_pools = await response.json()
        except (ClientConnectionError, ContentTypeError, InvalidURL):
            logger.warning(
                "Could not query the tractor pool list, the config is unreachable"
            )
            tractor_pools = {"BladeProfiles": []}

        # Build list of profile names to ignore
        PROFILE_IGNORE = [
            "DEV",
            "BUG",
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

        # Filter the pools
        pools = [
            profile["ProfileName"]
            for profile in tractor_pools["BladeProfiles"]
            if profile.get("ProfileName") not in PROFILE_IGNORE
        ]

        # Sort the pools
        pools.sort()

        pool_parameter = self.command_buffer.parameters["pools"]
        project_parameter = self.command_buffer.parameters["project"]

        pool_parameter.rebuild_type(*pools)

        # If user have a project
        if "project" in action_query.context_metadata:
            # Use the project as value
            project_parameter.rebuild_type(action_query.context_metadata["project"])
            project_parameter.hide = True
        else:
            # If there is no project in the current context return a hard coded list of project for 4th years
            project_parameter.rebuild_type("WS_Environment", "WS_Lighting")
