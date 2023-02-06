"""




To test :
rez env silex_client pycharm testpipe -- silex action tester


Sublit test :
rez env silex_client pycharm testpipe -- silex action submit --task-id 5d539ee9-1f09-4792-8dfe-343c9b411c24

FOr these tests check if the silex_client rez package is resolved to the dev version (work on a copy in dev_packages)

"""

from __future__ import annotations

import logging
import traceback
import os
import typing
from typing import Any, Dict, List, cast
import asyncio

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils import farm, command_builder
from silex_client.utils.log import flog
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from Deadline.DeadlineConnect import DeadlineCon
import aiohttp


class SubmitToDeadlineCommand(CommandBase):
    """
    Send job to Deadline
    """

    parameters = {
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
        },
        "frame_range": {
            "Label": "Frame Range",
            "type": FrameSet,
            "hide": True
        },
        "job_title": {
            "label": "Job title",
            "type": str,
            "value": "untitled",
            "hide": True,
        },
        "groups": {
            "label": "Groups",
            "type": SelectParameterMeta(),
            "hide": False,
        },
        "pools": {
            "label": "Pool",
            "type": SelectParameterMeta(),
            "hide": False,
        },
        "command": {
            "type": str,
            "hide": True
        }
    }

    async def setup(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        '''
        Setup parameters by querying the Deadline rapository
        '''
        if "deadline_query_groups_pools" not in action_query.store:
            try:
                async with aiohttp.ClientSession() as session:
                    # RestAPI Queries
                    deadline_group_url = 'http://localhost:8081/api/groups'
                    async with session.get(deadline_group_url) as response:
                        deadline_groups = await response.json()

                async with aiohttp.ClientSession() as session:
                    deadline_group_url = 'http://localhost:8081/api/pools'
                    async with session.get(deadline_group_url) as response:
                        deadline_pools = await response.json()

            except Exception as e:
                # TODO: Catch specific exceptions
                logger.error(
                    "Could not connect to Deadline WebService and query Groups and Pool information: "
                    + traceback.format_exc()
                )

            # Populate groups parameter with Deadline Groups
            self.command_buffer.parameters['groups'].rebuild_type(*deadline_groups)
            self.command_buffer.parameters['groups'].value = deadline_groups
            # Populate pools parameter with Deadline pools
            self.command_buffer.parameters['pools'].rebuild_type(*deadline_pools)
            self.command_buffer.parameters['pools'].value = deadline_pools

            # Store the query so it doesn't get executed unnecessarily

            action_query.store["deadline_query_groups_pools"] = True

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        # Connect to Deadline Web Service
        deadline = DeadlineCon('localhost', 8081)

        logger.info(f"Deadline : {deadline}")

        # Get user context info & convert to Deadline user name
        context = action_query.context_metadata
        user = cast(str, context["user"]).lower().replace(' ', '.')

        # Deadline Job Info

        JobInfo = {
            "Name": parameters["job_title"],
            "UserName": user,
            "Frames": parameters['frame_range'].frange,
            "ChunkSize": parameters['task_size'],
            "Group": parameters['groups'],
            "Pool": parameters['pools'],
            "Plugin": "CommandLine",
        }

        # truncate "rez" from command because Deadline CommandLine plugin uses rez.exe
        cmd = parameters['command']
        cmd = cmd.split(' ', 1)[1]

        PluginInfo = {
            "Executable": "C:\\rez\\__install__\\Scripts\\rez\\rez.exe",
            "Arguments": f"{cmd}"
        }

        new_job = deadline.Jobs.SubmitJob(JobInfo, PluginInfo)
        flog.info(new_job)
