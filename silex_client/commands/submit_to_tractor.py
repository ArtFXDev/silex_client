from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List

import gazu.project
from silex_client.action.command_base import CommandBase
from silex_client.utils import command_builder
from silex_client.utils.parameter_types import (
    DictParameterMeta,
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    UnionParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import tractor.api.author as author


class TractorSubmiter(CommandBase):
    """
    Send job to Tractor
    """

    # Service key filters for Tractor job
    # See: https://rmanwiki.pixar.com/display/TRA/Job+Scripting#JobScripting-servicekeys
    SERVICE_FILTERS = {
        "16RAM": "(@.mem >= 0) && (@.mem < 32)",
        "32RAM": "(@.mem >= 32) && (@.mem < 64)",
        "64RAM": "(@.mem >= 64) && (@.mem < 128)",
    }

    parameters = {
        "precommands": {
            "label": "Pre-commands list",
            "type": ListParameterMeta(command_builder.CommandBuilder),
            "value": [],
            "hide": True,
        },
        "postcommands": {
            "label": "Post-commands list",
            "type": ListParameterMeta(command_builder.CommandBuilder),
            "value": [],
            "hide": True,
        },
        "task_cleanup_cmd": {
            "label": "Task cleanup command",
            "type": UnionParameterMeta([command_builder.CommandBuilder]),
            "value": None,
            "hide": True,
        },
        "commands": {
            "label": "Commands list",
            "type": DictParameterMeta(
                str, DictParameterMeta(str, command_builder.CommandBuilder)
            ),
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
            "value": list(SERVICE_FILTERS.values()),
        },
        "blade_and_filters": {
            "label": "Restrict with filters",
            "type": MultipleSelectParameterMeta("GPU", "REDSHIFT", "VRAYHOU52"),
            "value": [],
        },
        "blade_ignore_filters": {
            "label": "Do not render on",
            "type": MultipleSelectParameterMeta("PC2014", "PC2015"),
            "value": ["PC2014", "PC2015"],
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

    def get_mount_command(self, nas: str) -> command_builder.CommandBuilder:
        """
        Constructs the mount command in order to access files on the render farm
        """
        mount_cmd = command_builder.CommandBuilder(
            "mount_rd_drive",
            delimiter=None,
            dashes="",
            rez_packages=["mount_render_drive"],
        )

        mount_cmd.value(nas)
        return mount_cmd

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
                samehost=1,
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
        precommands: List[command_builder.CommandBuilder] = parameters["precommands"]
        commands = parameters["commands"]
        blade_or_filters: List[str] = parameters["blade_or_filters"]
        blade_and_filters: List[str] = parameters["blade_and_filters"]
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

        # Add and && conditions
        ignore_keys = [f"!{k}" for k in (["BUG"] + parameters["blade_ignore_filters"])]
        if len(blade_and_filters) + len(ignore_keys) > 0:
            services = self.join_svckey_filters(
                [services] + blade_and_filters + ignore_keys, "&&"
            )

        # Create a job
        job = author.Job(
            title=job_title,
            priority=priority,
            tags=job_tags,
            projects=[context["project"]],
            service=services,
        )

        # Add the mount command
        if parameters["add_mount"] and context["project_nas"] is not None:
            mount_cmd = self.get_mount_command(context["project_nas"])
            precommands.append(mount_cmd)

        # Directory mapping for Linux
        # job.newDirMap("P:", f"/mnt/{nas}", "NFS")

        # This will organize tasks in group of tasks with dependencies
        for task_group_title, subtasks in commands.items():
            task_group: author.Task = author.Task(title=task_group_title)

            for subtask_title, subtask_cmd in subtasks.items():
                task = await self.create_task_with_commands(
                    parameters=parameters,
                    title=subtask_title,
                    project=action_query.context_metadata["project"].lower(),
                    command=subtask_cmd,
                )
                task_group.addChild(task)

            # Add the task as child
            job.addChild(task_group)

        # Submit the job to Tractor
        jid = job.spool(owner=owner)
        logger.info(f"Sent job: {job_title} ({jid})")
