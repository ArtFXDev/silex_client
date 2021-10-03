from __future__ import annotations
import socketio
import typing

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.network.websocket import WebsocketConnection


class WebsocketNamespace(socketio.AsyncClientNamespace):
    namespace = ""

    def __init__(
        self, namespace: str, context_metadata: dict, ws_connection: WebsocketConnection
    ):
        super().__init__(namespace)
        self.context_metadata = context_metadata
        self.ws_connection = ws_connection
        self.url = ws_connection.url

    def send(self, event: str, data: typing.Any):
        self.ws_connection.send(self.namespace, event, data)
