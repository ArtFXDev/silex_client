"""
@author: TD gang

Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

import asyncio
from threading import Thread

import websockets

from silex_client.utils.context import context
from silex_client.utils.log import logger


class WebsocketClient():
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages
    """
    def __init__(self, url="ws://localhost:8080"):
        self.is_running = False
        self.thread = None
        self.url = url
        self.loop = asyncio.new_event_loop()

    async def _receive_message(self):
        """
        Connect to the server, wait for the incomming messages and handle disconnection
        """
        try:
            async with websockets.connect(self.url) as websocket:
                await websocket.send(str(context.metadata))
                while True:
                    try:
                        message = await websocket.recv()
                        # The queue of incomming message is already handled by the library
                        await self._handle_message(message)
                    except websockets.ConnectionClosed:
                        logger.warning(
                            "Websocket connection on %s lost retrying...", self.url)
                        # Restart the loop to retry connection
                        await asyncio.sleep(1)
                        self.loop.create_task(self._receive_message())
                        break
        except OSError:
            logger.warning("Could not connect to %s retrying...", self.url)
            # Restart the loop to retry connection
            await asyncio.sleep(1)
            self.loop.create_task(self._receive_message())

    async def _handle_message(self, message):
        """
        Parse the incomming messages and run appropriate function
        """
        # TODO: Define a json protocol and handle the messages accordingly
        logger.info("Websocket message recieved : %s", message)
        print('Active tasks count: ', len([task for task in asyncio.Task.all_tasks() if not task.done()]))

    def _start_loop(self, loop):
        """
        Set the event loop for the current thread and run it
        This method is called by self.run() or self.run_multithreaded()
        """
        asyncio.set_event_loop(loop)
        self.loop.create_task(self._receive_message())
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Caught keyboard interrupt, stopping server...")
            self.stop()

    def run(self):
        """
        Initialize the event loop's task and run it in main thread
        """
        if self.is_running:
            logger.warn("Websocket server already running")
            return

        self.is_running = True
        self._start_loop(self.loop)


    def run_multithreaded(self):
        """
        Initialize the event loop's task and run it in a different thread
        """
        if self.is_running:
            logger.warn("Websocket server already running")
            return

        self.is_running = True
        self.thread = Thread(target=lambda: self._start_loop(self.loop))
        self.thread.start()

    def stop(self):
        """
        Stop the event loop event loop wherever it was run from
        (main thread or other thread)
        """
        if not self.is_running:
            logger.info("Websocket server was not running")
            return

        # Clear the loop
        self.loop.stop()
        # TODO: Find a way to clear the loop instead of let it get garbage collected
        self.loop = asyncio.new_event_loop()
        # If the loop was running in a different thread stop it
        if self.thread is not None:
            self.thread.join()
        self.is_running = False
