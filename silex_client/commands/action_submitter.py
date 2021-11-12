from __future__ import annotations
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

import tractor.api.author as author



class ActionSubmitter(CommandBase):
    """ 
    Copy file and override if necessary
    """

    parameters = {
        "action": {
            "label": "Action",
            "type": str,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):

        author.setEngineClientParam(debug=True)

        action: str = parameters.get("action")

        job = author.Job(title="job test")
        job.newTask(title="test task",
                    argv=["rez", "env", "silex_client",
                        "--", "silex", "action", action],
                    service="TD")

        jid = job.spool()
