"""
@author: TD gang

Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

import asyncio
import websockets

from silex_client.utils.context import context
from silex_client.utils.log import logger


class WebsocketHandler():
    """
    Server that connect the the given url throught websockets,
    receive and handle the incomming messages
    """
    def __init__(self, url="ws://localhost:8080"):
        self.loop = asyncio.get_event_loop()
        self.url = url
        self.loop = asyncio.get_event_loop()

    async def receive_message(self):
        """
        Connect to the server, wait for the incomming messages and handle disconnection
        """
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.send(str(context.metadata))
                while True:
                    try:
                        message = await websocket.recv()
                        await self.handle_message(message)
                    except websockets.ConnectionClosed:
                        logger.warning(
                            "Websocket connection on {self.url} lost")
                        asyncio.get_running_loop().stop()
        except Exception as ex:
            logger.warning(f"Could not connect to {self.url} retrying...")
            await asyncio.sleep(1)
            self.loop.create_task(self.receive_message())

    async def handle_message(self, message):
        """
        Parse the incomming messages and run appropriate function
        """
        # TODO: Define a json protocol and handle the messages accordingly
        logger.info(f"Websocket message recieved : {message}")

    def run(self):
        """
        Initialize the event loop's task and run the event loop
        """
        self.loop.create_task(self.receive_message())
        self.loop.run_forever()
