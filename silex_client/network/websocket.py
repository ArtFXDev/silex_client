"""
@author: TD gang

Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

from __future__ import annotations

import asyncio
import json
from concurrent import futures
from typing import Any, Dict, TYPE_CHECKING

import socketio
from socketio.exceptions import ConnectionError

from silex_client.network.websocket_action import WebsocketActionNamespace
from silex_client.network.websocket_dcc import WebsocketDCCNamespace
from silex_client.utils.log import logger
from silex_client.utils.serialiser import silex_encoder

# Forward references
if TYPE_CHECKING:
    from silex_client.core.context import Context


class WebsocketConnection:
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages
    """

    #: How long to wait for a confirmation fom every messages sent
    MESSAGE_CALLBACK_TIMEOUT = 1

    def __init__(self, url: str, context: Context):
        self.url = url

        self.socketio = socketio.AsyncClient()
        self.event_loop = context.event_loop

        # Register the different namespaces
        self.dcc_namespace = WebsocketDCCNamespace("/dcc", context, self)
        self.socketio.register_namespace(self.dcc_namespace)
        self.action_namespace = WebsocketActionNamespace("/dcc/action", context, self)
        self.socketio.register_namespace(self.action_namespace)

    @property
    def is_running(self):
        return self.socketio.connected

    async def _connect_socketio(self) -> None:
        try:
            await asyncio.wait_for(self.socketio.connect(self.url), 2)
        except (asyncio.TimeoutError, ConnectionError):
            logger.error(
                "Connection with the websocket server could not be established"
            )

    async def _disconnect_socketio(self) -> None:
        await self.socketio.disconnect()

    def start(self) -> futures.Future:
        """
        initialize the event loop's task and run it in main thread
        """
        if self.is_running:
            logger.warning(
                "Could not start websocket connection: The connection is already running"
            )
            future: futures.Future = futures.Future()
            future.set_result(None)
            return future

        future = self.event_loop.register_task(self._connect_socketio())
        futures.wait([future])
        return future

    def stop(self) -> futures.Future:
        """
        Ask to all the event loop's tasks to stop and join the thread to the main thread
        if there is one running
        """
        if not self.is_running:
            future: futures.Future = futures.Future()
            future.set_result(None)
            return future

        future = self.event_loop.register_task(self._disconnect_socketio())
        futures.wait([future])
        return future

    def send(self, namespace: str, event: str, data: Any = None) -> futures.Future:
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

    async def async_send(self, namespace, event, data=None) -> asyncio.Future:
        """
        Send a message using websocket from within the event loop
        """
        future = self.event_loop.loop.create_future()

        def callback(response):
            if not future.cancelled():
                future.set_result(response)

        logger.debug("Websocket client sending %s at %s on %s", data, namespace, event)
        await self.socketio.emit(event, data, namespace, callback)
        # Make sure a confirmation has been received
        try:
            await asyncio.wait_for(future, timeout=self.MESSAGE_CALLBACK_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(
                "The message %s has been sent on %s at %s but no confirmation has been received",
                data,
                namespace,
                event,
            )
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
