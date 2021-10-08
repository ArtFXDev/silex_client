"""
@author: TD gang

Base class for all the websocket namespaces
"""


from __future__ import annotations

import typing

import socketio

from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection


class WebsocketNamespace(socketio.AsyncClientNamespace):
    """
    Base class for all the websocket namespaces
    """

    namespace = ""

    def __init__(
        self, namespace: str, context_metadata: dict, ws_connection: WebsocketConnection
    ):
        super().__init__(namespace)
        self.context_metadata = context_metadata
        self.ws_connection = ws_connection
        self.url = ws_connection.url

    def send(self, event: str, data: typing.Any):
        """
        Add a message to the queue of message to send
        """
        self.ws_connection.send(self.namespace, event, data)

    async def on_connect(self):
        """
        Register the dcc on the silex service on connection
        """
        logger.info("Connected to %s on %s", self.url, self.namespace)

    async def on_disconnect(self):
        """
        Simply inform the user that the silex service is disconnected
        """
        logger.info("Disconected from %s on %s", self.url, self.namespace)
