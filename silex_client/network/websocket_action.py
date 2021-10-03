from silex_client.network.websocket_namespace import WebsocketNamespace
from silex_client.utils.log import logger


class WebsocketActionNamespace(WebsocketNamespace):
    namespace = "/dcc/action"

    async def on_query(self):
        logger.info("Query request received from %s", self.url)

    async def on_update(self):
        logger.debug("Action update received from %s", self.url)
