import socketio

from silex_client.utils.log import logger


class WebsocketActionNamespace(socketio.AsyncClientNamespace):
    def __init__(self, namespace: str, context_metadata: dict, url:str):
        super().__init__(namespace)
        self.context_metadata = context_metadata
        self.url = url

    async def on_query(self):
        logger.info("Query request received from %s", self.url)

    async def on_update(self):
        logger.debug("Action update received from %s", self.url)

