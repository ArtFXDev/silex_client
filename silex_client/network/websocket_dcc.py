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
        self.send("initialization", self.context_metadata)
