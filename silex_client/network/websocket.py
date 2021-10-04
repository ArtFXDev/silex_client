"""
@author: TD gang
Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""
from __future__ import annotations

import asyncio
import json
import typing
from concurrent import futures
from typing import Any, Dict, TYPE_CHECKING

import socketio

from silex_client.network.websocket_action import WebsocketActionNamespace
from silex_client.network.websocket_dcc import WebsocketDCCNamespace
from silex_client.utils.log import logger
from silex_client.utils.serialiser import silex_encoder

# Forward references
if TYPE_CHECKING:
    from silex_client.core.event_loop import EventLoop


class WebsocketConnection:
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages
    """

    def __init__(
        self,
        event_loop: EventLoop,
        context_metadata: dict = None,
        url: str = "ws://127.0.0.1:5118",
    ):
        self.is_running = False
        self.url = url

        self.socketio = socketio.AsyncClient()
        self.event_loop = event_loop

        # Set the default context
        if context_metadata is None:
            context_metadata = {}

        # Register the different namespaces
        self.dcc_namespace = self.socketio.register_namespace(
            WebsocketDCCNamespace("/dcc", context_metadata, self)
        )
        self.action_namespace = self.socketio.register_namespace(
            WebsocketActionNamespace("/dcc/action", context_metadata, self)
        )

    async def _connect_socketio(self) -> None:
        self.is_running = True
        await self.socketio.connect(self.url)

    async def _disconnect_socketio(self) -> None:
        await self.socketio.disconnect()
        self.is_running = False

    def start(self) -> None:
        """
        initialize the event loop's task and run it in main thread
        """
        if self.is_running:
            logger.warning(
                "Could not start websocket connection: The connection is already running"
            )
            return

        self.event_loop.register_task(self._connect_socketio())

    def stop(self) -> None:
        """
        Ask to all the event loop's tasks to stop and join the thread to the main thread
        if there is one running
        """
        if not self.is_running:
            return

        self.event_loop.register_task(self._disconnect_socketio())

    def send(self, namespace: str, event: str, data: Any) -> futures.Future:
        """
        Send a message using websocket from a different thread than the event loop
        """
        try:
            data = json.loads(json.dumps(data, default=silex_encoder))
        except TypeError:
            logger.error("Could not send %s: The data is not json serialisable", data)
            future: futures.Future = futures.Future()
            future.set_result(None)
            return future

        return self.event_loop.register_task(self.async_send(namespace, event, data))

    async def async_send(self, namespace, event, data) -> asyncio.Future:
        logger.debug("Websocket client sending %s at %s on %s", data, namespace, event)

        future = self.event_loop.loop.create_future()

        def callback(response):
            if not future.cancelled():
                future.set_result(response)

        await self.socketio.emit(event, data, namespace, callback)
        return future

    @staticmethod
    def url_to_parameters(url: str) -> Dict[str, str]:
        """
        Convert an url into a dict of key/value for all the parameters of the url
        """
        output: Dict[str, str] = {}
        # Split the path from the parameters
        splitted_url = url.split("?")
        # If there is no parameters return empty
        if len(splitted_url) != 2:
            return output
        # Split all the parameters and their variables and values
        parameters = splitted_url[1]
        for parameter in parameters.split("&"):
            splitted_parameter = parameter.split("=")
            if len(splitted_parameter) == 2:
                output[splitted_parameter[0]] = splitted_parameter[1]

        return output

    @staticmethod
    def parameters_to_url(base_url: str, parameters: Dict[str, str]) -> str:
        """
        Convert a dictionary of parameters to an url
        """
        output = base_url
        # If there is not parameters given just return the base url
        if len(parameters) < 1:
            return output

        # Concatenate all the parameters to te base url
        output += "?"
        for key, value in parameters.items():
            output += f"{key}={value}&"
        # Remove the dandeling '&'
        output = output[:-1]

        return output
