from __future__ import annotations
import asyncio
import typing

from silex_client.action.command_base import CommandBase
from typing import Any
from silex_client.utils.log import logger
from silex_client.utils.enums import Status

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

class SendMessage(CommandBase):
    """
    Send a message to the UI from websocket
    """

    parameters = {
        "message": {
            "label": "Message",
            "type": str,
            "value": None
        },
        "namespace": {
            "label": "Namespace",
            "type": str,
            "value": None
        },
        "event": {
            "label": "Event",
            "type": str,
            "value": None
        },
        "timeout": {
            "label": "Timeout",
            "type": float,
            "value": 0
        }
    }

    @CommandBase.conform_command()
    async def __call__(self, upstream: Any, parameters: dict, action_query: ActionQuery):
        response = await action_query.ws_connection.async_send(parameters["namespace"], parameters["event"], parameters["message"])
        # If wait_response is on, await the response of the UI
        if parameters["wait_response"]:
            if parameters["timeout"] > 0:
                try:
                    return await asyncio.wait_for(response, parameters["timeout"])
                except asyncio.TimeoutError:
                    logger.warning("Continuning action execution: timeout reached")
            else:
                return await response


class SendActionBuffer(CommandBase):
    """
    Send the action buffer to update the UI
    """

    parameters = {
        "wait_response": {
            "label": "Wait for a response",
            "type": bool,
            "value": False
        },
        "timeout": {
            "label": "Timeout",
            "type": float,
            "value": 0
        }
    }

    @CommandBase.conform_command()
    async def __call__(self, upstream: Any, parameters: dict, action_query: ActionQuery):
        response = await action_query.async_update_websocket()
        # If wait_response is on, await the response of the UI
        if parameters["wait_response"]:
            if parameters["timeout"] > 0:
                try:
                    return await asyncio.wait_for(response, parameters["timeout"])
                except asyncio.TimeoutError:
                    logger.warning("Error during action execution: timeout reached")
                    self.command_buffer.status = Status.COMPLETED
            else:
                return await response
