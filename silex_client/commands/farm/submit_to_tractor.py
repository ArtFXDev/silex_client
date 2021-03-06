from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List, cast

from silex_client.action.command_base import CommandBase
from silex_client.utils import farm
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
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
        "project": {"label": "Project", "type": SelectParameterMeta()},
        "priority": {
            "label": "Job type",
            "type": RadioSelectParameterMeta(
                **{
                    "Standard": 100,
                    "Specific frames": 128,
                    "Retake": 90,
                    "Static frame": 130,
                    "Supervision high": 125,
                    "Supervision low": 124,
                    "MOF & demoreel": 50,
                    "Personal project": 30,
                }
            ),
        },
        "min_blade_ram": {
            "label": "Min RAM needed",
            "tooltip": "Amount of available RAM for a blade to take a task",
            "type": RangeParameterMeta(
                start=0, end=64, increment=2, value_label="GB", marks=True, n_marks=4
            ),
            "value": 8,
        },
        "blade_and_filters": {
            "label": "Restrict with filters",
            "type": MultipleSelectParameterMeta(),
            "value": [],
        },
        "blade_ignore_filters": {
            "label": "Don't render on",
            "type": MultipleSelectParameterMeta(),
            "value": ["PC2014", "PC2015", "RTXQUADRO"],
        },
        "blade_blacklist": {
            "type": ListParameterMeta(str),
            "hide": True,
            "value": ["BUG", "DONOTUSE"],
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
    }

    def join_svckey_filters(self, filters: List[str], op: str) -> str:
        """
        Combines service key filters with an operator
        Ex: ["GPU", "32RAM"], "||" -> "(GPU) || (32RAM)"
        """
        return f" {op} ".join([f"({f})" for f in filters])

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        tasks: List[farm.Task] = parameters["tasks"]
        blade_and_filters: List[str] = parameters["blade_and_filters"]
        blade_ignore_filters: List[str] = parameters["blade_ignore_filters"]
        blade_blacklist: List[str] = parameters["blade_blacklist"]
        job_title: str = parameters["job_title"]
        job_tags: List[str] = parameters["job_tags"]
        priority: float = float(parameters["priority"])

        # Get user context information
        context = action_query.context_metadata
        owner = cast(str, context["user_email"]).split("@")[0]

        # Filter by available RAM
        services = f"@.mem >= {parameters['min_blade_ram']}"

        # Ignore services and blacklist
        ignore_services = [f"!{s}" for s in blade_ignore_filters + blade_blacklist]

        # Add and && conditions
        if len(blade_and_filters) > 0 or len(ignore_services) > 0:
            all_services = [services] + blade_and_filters + ignore_services
            services = self.join_svckey_filters(all_services, "&&")

        # Get project from context or from parameter in case the submit was launched without a context
        project = context.get("project", parameters["project"])

        # Create a Tractor job
        job = author.Job(
            title=job_title,
            priority=priority,
            tags=job_tags,
            projects=[project],
            service=services,
        )

        # Add the tasks to the job by converting them to Tractor specific classes
        for task in tasks:
            job.addChild(convert_to_tractor_task(task))

        # Submit the job to Tractor
        job.spool(owner=owner)

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if "tractor_query_pool" not in action_query.store:
            tractor_pools: Dict[str, List[Dict[str, str]]] = {"BladeProfiles": []}

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

            service_keys = [
                svckey
                for profile in tractor_pools["BladeProfiles"]
                if "Provides" in profile
                for svckey in profile["Provides"]
            ]

            # Filter the services
            service_keys = list(set(service_keys) - set(parameters["blade_blacklist"]))

            service_keys.sort()
            blade_ignore_filters = self.command_buffer.parameters[
                "blade_ignore_filters"
            ]
            blade_ignore_filters.rebuild_type(*service_keys)

            blade_and_filters = self.command_buffer.parameters["blade_and_filters"]
            blade_and_filters.rebuild_type(*service_keys)

            action_query.store["tractor_query_pool"] = True

        # Project selector
        project_selector = self.command_buffer.parameters["project"]
        project_in_context = "project" in action_query.context_metadata

        project_selector.hide = project_in_context

        # Rebuilt selector with project values
        if not project_in_context:
            project_selector.rebuild_type(
                *[p["name"] for p in action_query.context_metadata["user_projects"]]
            )
