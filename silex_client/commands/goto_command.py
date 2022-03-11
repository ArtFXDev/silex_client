from __future__ import annotations

import logging
import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.enums import Status

if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class GoToCommand(CommandBase):
    """
    Exit the selected commands by setting all the commands to skip
    The command can be selected by name or by count. If no name is specified, the count
    is used.
    """

    parameters = {
        "name": {
            "label": "Name of the command to go to",
            "type": str,
            "value": "",
        },
        "count": {
            "type": int,
            "label": "Quantity of command to skip",
            "tooltip": "The count start at the current command, "
            + "(1 will skip the current command, which will do nothing)",
            "value": 1,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        name: str = parameters["name"]
        count: int = parameters["count"]

        current_command = self.command_buffer
        current_command_index = action_query.commands.index(current_command)

        goto_command_index = current_command_index + count
        if name:
            for index, command in enumerate(
                action_query.commands[current_command_index:]
            ):
                if name and command.name == name:
                    goto_command_index += index

        for command in action_query.commands[current_command_index:goto_command_index]:
            if command.status is Status.COMPLETED:
                continue
            command.skip = True
