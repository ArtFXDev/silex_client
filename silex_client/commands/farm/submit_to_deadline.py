"""




To test :
rez env silex_client pycharm testpipe -- silex action tester


Sublit test :
rez env silex_client pycharm testpipe -- silex action submit --task-id 5d539ee9-1f09-4792-8dfe-343c9b411c24

FOr these tests check if the silex_client rez package is resolved to the dev version (work on a copy in dev_packages)

"""


from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List, cast
import asyncio

from silex_client.action.command_base import CommandBase
from silex_client.utils import farm, command_builder
from silex_client.utils.log import logger
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

import gazu.user

class SubmitToDeadlineCommand(CommandBase):
    """
    Send job to Deadline
    """

    # parameters = {
    #     "message": {
    #         "label": "message",
    #         "type": str,
    #     }}


    parameters = {
        "message": {
            "type": str,
        },
        "something": {
            "type": str,
        }
    }
    """
    "tasks": {
        "label": "Tasks list",
        "type": ListParameterMeta(str),
        "hide": True,
    },
    "job_title": {
        "label": "Job title",
        "type": str,
        "value": "untitled",
        "hide": True,
    }
    }
    """

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        print("Inside Submit Call")
        logger.info("Inside Submit Call")
    # Connect to Deadline Web Service
        deadline = DeadlineCon('localhost', 8081)

        logger.info(f"Deadline : {deadline}")

    # Get user context info & convert to Deadline user name
        context = action_query.context_metadata
        user = cast(str, context["user"]).lower().replace(' ', '.')

        logger.info(f"USer : {user}")

        from pprint import pformat
        logger.info(pformat(parameters))


    # DUMMY JOB INFO to test

    # Deadline Job Info
        JobInfo = {
            "Name": parameters["job_title"],
            "UserName": user,
            "Frames": "0-1",
            "Plugin": "CommandLine"

        }

    # Get render command
    

        # PluginInfo = {
        #     "Executable": "C:\\rez\\__install__\\Scripts\\rez\\rez-env.exe",
        #     "Arguments": f'''testpipe python -- python -c "print('{parameters["message"]}')"'''
        # }

        PluginInfo = {
            "ShellExecute": True,
            "Shell": "cmd",
            "Arguments": f'''{parameters['tasks'][0].commands[0]}'''
        }
        logger.debug(parameters['tasks'][0].commands)

        new_job = deadline.Jobs.SubmitJob(JobInfo, PluginInfo)
