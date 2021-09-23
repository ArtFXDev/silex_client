from silex_client.utils.log import logger
from silex_client.network.websocket_namespace import WebsocketNamespace


class WebsocketDCCNamespace(WebsocketNamespace):
    namespace = "/dcc"

    async def on_connect(self):
        logger.info("Connected to %s", self.url)
        self.send("initialization", self.context_metadata)

    async def on_disconnect(self):
        logger.info("Disconected from %s", self.url)
