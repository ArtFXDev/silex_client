from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List

from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder, farm
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    UnionParameterMeta,
)
from silex_client.utils.tractor import convert_to_tractor_task

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

# Service key filters for Tractor job
# See: https://rmanwiki.pixar.com/display/TRA/Job+Scripting#JobScripting-servicekeys
SERVICE_FILTERS = {
    "16RAM": "(@.mem >= 0) && (@.mem < 8)",
    "32RAM": "(@.mem >= 8) && (@.mem < 16)",
    "64RAM": "(@.mem >= 16)",
}


class SubmitToTractorCommand(CommandBase):
    """
    Send job to Tractor
    """

    parameters = {
        "tasks": {
            "label": "Tasks list",
            "type": ListParameterMeta(farm.Task),
            "hide": True,
        },
        "priority": {
            "label": "Job type",
            "type": RadioSelectParameterMeta(
                **{
                    "Standard": 100,
                    "Specific frames": 120,
                    "Retake": 90,
                    "Camap": 130,
                }
            ),
        },
        "blade_or_filters": {
            "label": "Render on",
            "type": MultipleSelectParameterMeta(**SERVICE_FILTERS),
            "value": [SERVICE_FILTERS[k] for k in ["16RAM", "32RAM", "64RAM"]],
        },
        "blade_and_filters": {
            "label": "Restrict with filters",
            "type": MultipleSelectParameterMeta(),
            "value": [],
        },
        "blade_ignore_filters": {
            "label": "Don't render on",
            "type": MultipleSelectParameterMeta(),
            "value": ["PC2014", "PC2015"],
        },
        "blade_blacklist": {
            "type": ListParameterMeta(str),
            "hide": True,
            "value": ["BUG"],
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "untitled",
            "hide": True,
        },
        "job_tags": {
            "type": ListParameterMeta(str),
            "hide": True,
        },
        "add_mount": {
            "type": bool,
            "value": True,
            "hide": True,
        },
    }

    def join_svckey_filters(self, filters: List[str], op: str) -> str:
        """
        Combines service key filters with an operator
        Ex: ["GPU", "32RAM"], "||" -> "(GPU) || (32RAM)"
        """
        return f" {op} ".join([f"({f})" for f in filters])

    async def create_task_with_commands(
        self,
        parameters: Dict[str, Any],
        title: str,
        project: str,
        command: command_builder.CommandBuilder,
    ):
        cleanup = parameters["task_cleanup_cmd"]
        task: author.Task = author.Task(title=title)

        # Add the project in the Rez requires
        # This is useful to require ACES and define OCIO for example
        command.add_rez_package(project)

        # Since Tractor's task.addCleanup doesn't work
        # We use a custom python wrapper script
        if cleanup is not None:
            command = (
                command_builder.CommandBuilder(
                    "python", rez_packages=["command_wrapper"], dashes="--"
                )
                .value("-m")
                .value("command_wrapper.main")
                .param("cleanup", f'"{str(cleanup)}"')
                .param("command", f'"{str(command)}"')
            )

        # Add pre and post commands to each subtask
        all_commands = (
            parameters["precommands"] + [command] + parameters["postcommands"]
        )

        # Add every command to the subtask
        for command in all_commands:
            task.newCommand(
                argv=command.as_argv(),
                # Run commands on the same host
                samehost=True,
                # Limit tags with rez packages
                # Useful when limiting the amout of vray jobs on the farm for example
                tags=command.rez_packages,
            )

        return task

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        tasks: List[farm.Task] = parameters["tasks"]
        blade_or_filters: List[str] = parameters["blade_or_filters"]
        blade_and_filters: List[str] = parameters["blade_and_filters"]
        blade_ignore_filters: List[str] = parameters["blade_ignore_filters"]
        blade_blacklist: List[str] = parameters["blade_blacklist"]
        job_title: str = parameters["job_title"]
        job_tags: List[str] = parameters["job_tags"]
        priority: float = float(parameters["priority"])

        # Get user context information
        context = action_query.context_metadata
        owner = context["user_email"].split("@")[0]

        # Construct service keys to restrict the blades the tasks will run on
        services = ""

        # Set the services the job will run on (groups of blades and filter tags using service keys)
        if len(blade_or_filters) > 0:
            services = self.join_svckey_filters(blade_or_filters, "||")

        ignore_services = [f"!{s}" for s in blade_ignore_filters + blade_blacklist]

        # Add and && conditions
        if len(blade_and_filters) > 0 or len(ignore_services) > 0:
            services = self.join_svckey_filters(
                [services] + blade_and_filters + ignore_services, "&&"
            )

        # Create a Tractor job
        job = author.Job(
            title=job_title,
            priority=priority,
            tags=job_tags,
            projects=[context["project"]],
            service=services,
        )

        # Directory mapping for Linux
        # job.newDirMap("P:", f"/mnt/{nas}", "NFS")

        # Add the tasks to the job by converting them to Tractor specific classes
        for task in tasks:
            job.addChild(convert_to_tractor_task(task))

        # Submit the job to Tractor
        jid = job.spool(owner=owner)
        logger.info(f"Sent job: {job_title} ({jid})")

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        tractor_pools = {"BladeProfiles": []}

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

        # Filter the pools
        service_keys = list(
            set(
                [
                    svckey
                    for profile in tractor_pools["BladeProfiles"]
                    if "Provides" in profile
                    for svckey in profile["Provides"]
                ]
            )
            - set(parameters["blade_blacklist"])
        )

        service_keys.sort()
        blade_ignore_filters = self.command_buffer.parameters["blade_ignore_filters"]
        blade_ignore_filters.rebuild_type(*service_keys)

        blade_and_filters = self.command_buffer.parameters["blade_and_filters"]
        blade_and_filters.rebuild_type(*service_keys)
