from __future__ import annotations
import typing

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger

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
        "wait_response": {
            "label": "Wait for a response",
            "type": bool,
            "value": False
        }
    }

    @CommandBase.conform_command()
    async def __call__(self, parameters: dict, action_query: ActionQuery):
        action_query.ws_connection.send(parameters["namespace"], parameters["event"], parameters["message"])


class SendActionBuffer(CommandBase):
    """
    Send the action buffer to update the UI
    """

    parameters = {
        "wait_response": {
            "label": "Wait for a response",
            "type": bool,
            "value": False
        }
    }

    @CommandBase.conform_command()
    async def __call__(self, parameters: dict, action_query: ActionQuery):
        action_query.send_websocket()

class ReceiveActionBuffer(CommandBase):
    """
    Wait for the UI to update the buffer
    """

    @CommandBase.conform_command()
    async def __call__(self, parameters: dict, action_query: ActionQuery):
        pass

