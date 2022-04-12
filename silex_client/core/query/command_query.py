"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

import asyncio
import copy
import os
from concurrent import futures
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

import jsondiff
from silex_client.graph.action import Action
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.datatypes import ReadOnlyDict
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger
from silex_client.utils.serialiser import silex_diff

# Forward references
if TYPE_CHECKING:
    from silex_client.graph.command import Command
    from silex_client.graph.step import Step
    from silex_client.core.event_loop import EventLoop
    from silex_client.network.websocket import WebsocketConnection


class CommandQuery:

    @staticmethod
    def get_commands_from_step(self, step: Step) -> Optional[Command]:
        """
        Gather all the commands in the action

        returns: Dict(command_index : command_object)
        """

        step_children = step.children
        commands: Dict[str, Command] = {}

        if len(stepn_children) > 1:
            logger.error(
            f"The step : {step.name}, has no children",
            )
            return None

        for child in step_children.values():
            if isinstance(child, Command):
                commands[child.index] = child

            if isinstance(child, Step):
                self.get_commands_from_step(child)

        return commands