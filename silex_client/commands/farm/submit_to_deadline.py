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
from typing import Any, Dict
from datetime import timedelta
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.utils.deadline.runner import DeadlineRunner
from silex_client.config.priority_rank import priority_rank

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SubmitToDeadlineCommand(CommandBase):
    """
    Send job to Deadline
    """

    parameters = {
        "jobs": {
            "type": list,
            "hide": True
        },
        "groups": {
            "label": "Groups",
            "type": SelectParameterMeta(),
            "hide": False,
        },
        "pools": {
            "label": "Pools",
            "type": SelectParameterMeta(),
            "hide": False,
        },
        "task_size": {
            "label": "Task size",
            "tooltip": "Number of frames per computer",
            "type": int,
            "value": 10,
            "hide": False
        },
        "priority_rank": {
            "label": "Priority rank",
            "type": SelectParameterMeta("normal", "camap", "test sampling", "priority sup", "retake", "making of",
                                        "personal"),
            "value": "normal",
            "hide": False
        },
        "delay": {
            "label": "Delay submit",
            "type": bool,
            "tooltip": "If true, job will be rendered in 5 minutes.",
            "value": False,
            "hide": False
        },
        "minutes":{
            'label': "Delay in minutes",
            "type": int,
            "value": 5,
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
        Setup parameters by querying the Deadline repository
        '''

        # get group and pool list
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

        # set hide about movie
        minutes = self.command_buffer.parameters.get('minutes')
        is_delay = self.command_buffer.parameters.get('delay')
        if not is_delay.get_value(action_query):
            minutes.hide = True
        else:
            minutes.hide = False

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):

        # Submit to Deadline Runner
        dr = DeadlineRunner()

        previous_job_id = None
        jobs = parameters.get('jobs')

        for job in jobs:
            # set job datas
            if job.depends_on_previous is True:
                job.set_dependency(previous_job_id)
            if parameters['delay'] is True:
                job.set_delay(parameters["minutes"])

            job.set_group(parameters['groups'])
            job.set_pool(parameters['pools'])
            job.set_chunk_size(parameters['task_size'])
            job.set_priority(priority_rank.get(parameters['priority_rank']))

            # run job
            previous_job_id = dr.run(job).get('_id')

        return {"jobs": jobs}
