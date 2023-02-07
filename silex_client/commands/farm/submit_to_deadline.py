"""




To test :
rez env silex_client pycharm testpipe -- silex action tester


Sublit test :
rez env silex_client pycharm testpipe -- silex action submit --task-id 5d539ee9-1f09-4792-8dfe-343c9b411c24

FOr these tests check if the silex_client rez package is resolved to the dev version (work on a copy in dev_packages)

"""

from __future__ import annotations

import logging
import typing
from typing import Any, Dict, List, cast

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils.log import flog
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.utils.deadline.job import DeadlineCommandLineJob
from silex_client.utils.deadline.runner import DeadlineRunner

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

from Deadline.DeadlineConnect import DeadlineCon


class SubmitToDeadlineCommand(CommandBase):
    """
    Send job to Deadline
    """

    parameters = {
        "task_size": {
            "type": int,
            "hide": True
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
            # TODO change to list of commands
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

        if 'deadline_query_groups_pools' not in action_query.store:

            deadline_groups = await DeadlineRunner.get_groups()
            deadline_pools = await DeadlineRunner.get_pools()

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

        # Get user context info & convert to Deadline username
        context = action_query.context_metadata
        user = cast(str, context["user"]).lower().replace(' ', '.')

        # truncate "rez" from command because Deadline CommandLine plugin uses rez.exe
        # TODO do for each command in case of several commands
        cmd = parameters['command']
        cmd = cmd.split(' ', 1)[1]



        submit_info = DeadlineCommandLineJob(
            parameters['job_title'],
            user,
            cmd,
            parameters['frame_range'],
            parameters['groups'],
            parameters['pools'],
            parameters['task_size']
        )

        # TODO Submit for every command received in case of batch job

        # Submit to Deadline Runner
        dr = DeadlineRunner()
        dr.run(submit_info)
