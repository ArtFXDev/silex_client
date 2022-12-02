from __future__ import annotations

import asyncio
import logging
import typing
from typing import Any, Dict

from fileseq import FrameSet
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    MultipleSelectParameterMeta,
    PathParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
    TaskFileParameterMeta,
    TaskParameterMeta,
    TextParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class InputTester(CommandBase):

    parameters = {
        "message": {
            "label": "Input Tester",
            "type": str,
            "value": "test",
            "tooltip": "Testing the string parameters",
        }
    }
    
    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):

        logger.info(parameters["message"])