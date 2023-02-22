from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List, cast
import asyncio

from silex_client.action.command_base import CommandBase
from silex_client.utils import farm, command_builder
from silex_client.utils.log import logger, flog
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

class ElouanSubmitterDeadline(CommandBase):
    parameters = {
        "message": {
            "label": "Input Tester",
            "type": str,
            "value": "test",
            "tooltip": "Testing the string parameters",
        },
        "helpme": {
            "label": "Input Tester",
            "type": str,
            "value": "test",
            "tooltip": "Testing the string parameters",
        },
    }

    flog.error("in the class")

    @CommandBase.conform_command()
    async def __call__(
            self,
            parameters: Dict[str, Any],
            action_query: ActionQuery,
            logger: logging.Logger,
    ):
        logger.info(parameters["message"])
        flog.info("hello")
        flog.error(parameters)

        return {"message": "yo man"}