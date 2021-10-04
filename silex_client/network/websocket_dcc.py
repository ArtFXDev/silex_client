"""
@author: TD gang

Definition of all the handlers for the namespace /dcc
This namespace is used to register the dcc into the silex service
"""

from silex_client.network.websocket_namespace import WebsocketNamespace
from silex_client.utils.log import logger


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
        logger.info("Connected to %s", self.url)
        self.send("initialization", self.context_metadata)

    async def on_disconnect(self):
        """
        Simply inform the user that the silex service is disconnected
        """
        logger.info("Disconected from %s", self.url)
