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
    from silex_client.core.context import Context
    from silex_client.network.websocket import WebsocketConnection


class WebsocketNamespace(socketio.AsyncClientNamespace):
    """
    Base class for all the websocket namespaces
    """

    namespace = ""

    def __init__(
        self, namespace: str, context: Context, ws_connection: WebsocketConnection
    ):
        super().__init__(namespace)
        self.context = context
        self.ws_connection = ws_connection
        self.url = ws_connection.url

    async def on_connect(self):
        """
        Register the dcc on the silex service on connection
        """
        logger.info("Connected to %s on %s", self.url, self.namespace)

    async def on_disconnect(self):
        """
        Simply inform the user that the silex service is disconnected
        """
        logger.info("Disconnected from %s on %s", self.url, self.namespace)
