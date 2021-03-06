"""
@author: TD gang

Definition of all the handlers for the namespace /dcc
This namespace is used to register the dcc into the silex service
"""

from silex_client.network.websocket_namespace import WebsocketNamespace


class WebsocketDCCNamespace(WebsocketNamespace):
    """
    Definition of all the handlers for the namespace /dcc
    This namespace is used to register the dcc into the silex service
    """

    namespace = "/dcc"

    async def on_connect(self):
        """
        Register the dcc on the silex service on connection
        """
        await super().on_connect()

        running_actions = self.context.running_actions
        running_actions = {
            key: value.buffer.serialize() for key, value in running_actions.items()
        }

        initialisation_data = {
            "context": self.context.metadata,
            "runningActions": running_actions,
        }

        await self.ws_connection.async_send(
            self.namespace, "initialization", initialisation_data
        )
