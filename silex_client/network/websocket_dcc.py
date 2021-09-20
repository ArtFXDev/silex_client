import socketio

from silex_client.utils.log import logger


class WebsocketDCCNamespace(socketio.AsyncClientNamespace):
    def __init__(self, namespace: str, context_metadata: dict, url:str):
        super().__init__(namespace)
        self.context_metadata = context_metadata
        self.url = url

    async def on_connect(self):
        logger.info("Connected to %s", self.url)
        await self.emit("initialisation", self.context_metadata)

    async def on_disconnect(self):
        logger.info("Disconected from %s", self.url)
