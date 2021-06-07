"""
@author: TD gang

Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

import asyncio
import gc
from contextlib import suppress
from threading import Thread

import websockets

from silex_client.utils.context import context
from silex_client.utils.log import logger


class WebsocketConnexion():
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages
    """
    def __init__(self, url="ws://localhost:8080"):
        self.is_running = False
        self.pending_stop = False
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
                while not self.pending_stop:
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

    def _start_loop(self, loop):
        """
        Set the event loop for the current thread and run it
        This method is called by self.run() or self.run_multithreaded()
        """
        if self.loop.is_running():
            logger.info("Event loop already running")
            return

        asyncio.set_event_loop(loop)
        try:
            self.loop.run_until_complete(self._receive_message())
        except KeyboardInterrupt:
            # Catch keyboard interrupt to allow stopping the event loop with ctrl+c
            self.stop()
        # Clean the event loop once completed
        self._clear_loop()
        self.pending_stop = False

    def _clear_loop(self):
        """
        Clear the event loop from its pending task and delete it
        """
        if self.loop.is_running():
            logger.info("The event loop needs to be stopped before being cleared")
            return

        #TODO: Find a way to clear the loop that works properly everytime
        logger.info("Clearing event loop...")
        # Clear the loop
        for task in asyncio.Task.all_tasks():
            # The cancel method will raise CancelledError on the running task to stop it
            task.cancel()
        # Wait for the task's cancellation in a suppress context to mute the CancelledError
        with suppress(asyncio.CancelledError):
            for task in asyncio.Task.all_tasks():
                self.loop.run_until_complete(task)
        # Create a new loop and let the old one get garbage collected
        self.loop = asyncio.new_event_loop()
        # Trigger the garbage collection
        gc.collect()

        self.is_running = False
        logger.info("Event loop cleared")

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
        if not self.is_running:
            logger.info("Websocket server was not running")
            return
        # Request the event loop to stop
        self.pending_stop = True
        # If the loop was running in a different thread stop it
        if self.thread is not None:
            self.thread.join(3)
            if self.thread.is_alive():
                logger.warn("Could not stop the websocket thread for %s", self.url)
            else:
                self.thread = None
    

server = WebsocketConnexion()
