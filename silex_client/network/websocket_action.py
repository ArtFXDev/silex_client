"""
@author: TD gang

Definition of all the handlers for the namespace /dcc/action
This namespace is used to reveive and send updates of the action execution
"""

from __future__ import annotations

import asyncio
from typing import Any, List, TYPE_CHECKING, Callable

from silex_client.network.websocket_namespace import WebsocketNamespace
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection


class WebsocketActionNamespace(WebsocketNamespace):
    """
    Definition of all the handlers for the namespace /dcc/action
    This namespace is used to reveive and send updates of the action execution
    """

    def __init__(
        self, namespace: str, context_metadata: dict, ws_connection: WebsocketConnection
    ):
        super().__init__(namespace, context_metadata, ws_connection)

        self.update_futures: List[asyncio.Future] = []
        self.query_futures: List[asyncio.Future] = []

    namespace = "/dcc/action"

    async def on_query(self, data):
        """
        Create an new action query
        """
        logger.info("Query request: %s received from %s", data, self.url)

        for future in self.query_futures:
            if not future.cancelled():
                future.set_result(data)

        self.query_futures.clear()

    async def on_update(self, data):
        """
        Update an already executing action
        """
        logger.debug("Action update: %s received from %s", data, self.url)

        for future in self.update_futures:
            if not future.cancelled():
                future.set_result(data)

        self.update_futures.clear()

    async def register_query_callback(
        self, coroutine: Callable[[asyncio.Future], Any]
    ) -> asyncio.Future:
        """
        Add a callback that is called at the next action query
        """
        event_loop = self.ws_connection.event_loop
        future = event_loop.loop.create_future()
        future.add_done_callback(coroutine)
        self.query_futures.append(future)
        return future

    async def register_update_callback(
        self, coroutine: Callable[[asyncio.Future], Any]
    ) -> asyncio.Future:
        """
        Add a callback that is called at the next update query
        """
        event_loop = self.ws_connection.event_loop
        future = event_loop.loop.create_future()
        future.add_done_callback(coroutine)
        self.update_futures.append(future)
        return future

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
