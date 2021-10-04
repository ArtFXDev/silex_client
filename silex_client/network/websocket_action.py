"""
@author: TD gang

Definition of all the handlers for the namespace /dcc/action
This namespace is used to reveive and send updates of the action execution
"""

from silex_client.network.websocket_namespace import WebsocketNamespace
from silex_client.utils.log import logger


class WebsocketActionNamespace(WebsocketNamespace):
    """
    Definition of all the handlers for the namespace /dcc/action
    This namespace is used to reveive and send updates of the action execution
    """

    namespace = "/dcc/action"

    async def on_query(self):
        """
        Create an new action query
        """
        logger.info("Query request received from %s", self.url)

    async def on_update(self):
        """
        Update an already executing action
        """
        logger.debug("Action update received from %s", self.url)
