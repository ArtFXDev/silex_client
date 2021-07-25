"""
@author: TD gang

Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

import asyncio
import gc
import time
from contextlib import suppress
from threading import Thread
from typing import List, Union, Dict, Any

from websockets import client
from websockets.exceptions import (ConnectionClosed, ConnectionClosedError,
                                   InvalidMessage)

from silex_client.utils.log import logger


class WebsocketConnection:
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages
    """

    # Defines how long each task will wait between every loop
    EVENT_LOOP_TIMEOUT = 0.5
    # Defines how long to wait for the thread to join
    THREAD_TEARDOWN_TIMEOUT = 8

    def __init__(self, url: str = None):
        self.is_running = False
        self.thread = None
        self.pending_stop = False
        self.pending_restart = False
        self.loop = asyncio.new_event_loop()
        self.pending_message = []

        # Set the url accordingly
        if url is None:
            url = "ws://localhost:8080"
        self.url = url

    async def _connect(self) -> None:
        """
        Connect to the server, wait for the incomming messages and handle disconnection
        Called by self.run() or self.run_multithreaded()
        """
        self.pending_restart = False
        logger.info("Connecting to %s", self.url)
        try:
            websocket = await client.connect(self.url)
            # Create two async tasks
            self.loop.create_task(self._listen_incomming(websocket))
            self.loop.create_task(self._listen_outgoing(websocket))
            # Listen to pending stop or restart
            while not self.pending_stop and not self.pending_restart:
                await asyncio.sleep(self.EVENT_LOOP_TIMEOUT)
        except (OSError, ConnectionResetError, InvalidMessage):
            logger.warning("Could not connect to %s retrying...", self.url)
            await asyncio.sleep(self.EVENT_LOOP_TIMEOUT)
            self.pending_restart = True

        logger.info("Leaving event loop...")

    async def _listen_incomming(
            self, websocket: client.WebSocketClientProtocol) -> None:
        """
        Async infinite loop waiting for messages to receive
        """
        while not self.pending_stop and not self.pending_restart:
            # The queue of incomming message is already handled by the library
            try:
                # Wait for a response with a timeout
                with suppress(asyncio.TimeoutError):
                    message = await asyncio.wait_for(websocket.recv(),
                                                     self.EVENT_LOOP_TIMEOUT)
                    logger.debug("Websocket client received %s" % message)
                    await self._handle_message(message)
            except (ConnectionClosed, ConnectionClosedError):
                # If the connection closed was not planned
                if not self.pending_stop:
                    logger.warning("Connection on %s lost retrying...",
                                   self.url)
                    self.pending_restart = True

    async def _listen_outgoing(
            self, websocket: client.WebSocketClientProtocol) -> None:
        """
        Async infinite loop waiting for messages to be sent
        """
        while not self.pending_stop and not self.pending_restart:
            # Send all the pending messges
            for message in self.pending_message:
                try:
                    logger.debug("Websocket client sending %s" % message)
                    await asyncio.wait_for(websocket.send(message),
                                           self.EVENT_LOOP_TIMEOUT)
                except (ConnectionClosed, ConnectionClosedError):
                    # If the connection closed was not planned
                    if not self.pending_stop:
                        logger.warning("Connection on %s lost retrying...",
                                       self.url)
                        self.pending_restart = True

            # Clear the pending_list
            self.pending_message.clear()
            # Sleep a bit between each iteration
            await asyncio.sleep(self.EVENT_LOOP_TIMEOUT)

    async def _handle_message(self, message: Any) -> None:
        """
        Parse the incomming messages and run appropriate function
        """
        # TODO: Define a json protocol and handle the messages accordingly
        if message == "ping":
            self.send("pong")
        else:
            logger.warning("No websocket message handler for : %s", message)

    def _start_loop(self) -> None:
        """
        Set the event loop for the current thread and run it
        This method is called by self.run() or self.run_multithreaded()
        """
        if self.loop.is_running():
            logger.info("Event loop already running")
            return

        while True:
            self.pending_stop = False
            self.pending_restart = False
            asyncio.set_event_loop(self.loop)
            connect_task = self.loop.create_task(self._connect())

            try:
                logger.debug("Starting websocket event loop")
                self.loop.run_until_complete(connect_task)
            except KeyboardInterrupt:
                # Catch keyboard interrupt to allow stopping the event loop with ctrl+c
                self.stop()

            # Clean the event loop once completed
            self._clear_loop()

            # If no restart is required leave the loop
            if not self.pending_restart or self.pending_stop:
                break

        self.is_running = False

    def _clear_loop(self) -> None:
        """
        Clear the event loop from its pending task and delete it
        This method is called by self._start_loop()
        """
        if self.loop.is_running():
            logger.info("The event loop must be stopped before being cleared")
            return

        # TODO: Find a way to clear the loop that works without warnings everytime
        # (the warning is ignored in the pytest.ini)
        logger.info("Clearing event loop...")
        # Clear the loop
        for task in asyncio.all_tasks(self.loop):
            # The cancel method will raise CancelledError on the running task to stop it
            task.cancel()
            # Wait for the task's cancellation in a suppress context to mute the CancelledError
            with suppress(asyncio.CancelledError, ConnectionClosedError,
                          ConnectionClosed):
                self.loop.run_until_complete(task)

        # Create a new loop and let the old one get garbage collected
        self.loop = asyncio.new_event_loop()
        # Trigger the garbage collection
        gc.collect()

        logger.info("Event loop cleared")

    def run(self) -> None:
        """
        Initialize the event loop's task and run it in main thread
        """
        if self.is_running:
            logger.warning("Websocket server already running")
            return

        self.is_running = True
        self._start_loop()

    def run_multithreaded(self):
        """
        Initialize the event loop's task and run it in a different thread
        """
        if self.is_running:
            logger.warning("Websocket server already running")
            return

        self.is_running = True
        self.thread = Thread(target=self._start_loop)
        self.thread.start()

    def stop(self) -> None:
        """
        Ask to all the event loop's tasks to stop and join the thread to the main thread
        if there is one running
        """
        if not self.is_running:
            logger.info("Websocket server was not running")
            return
        # Request the event loop to stop
        self.pending_stop = True

        # If the loop was running in a different thread stop it
        if self.thread is not None:
            self.thread.join(self.THREAD_TEARDOWN_TIMEOUT)
            if self.thread.is_alive():
                logger.warning("Could not stop the connection thread for %s",
                               self.url)
            else:
                self.thread = None

    def send(self, message: Union[str, List[str]]) -> None:
        """
        Add the given message to the list of pending message to be sent
        """
        if isinstance(message, str):
            self.pending_message.append(message)
        elif isinstance(message, list):
            self.pending_message.extend(message)

    @staticmethod
    def url_to_parameters(url: str) -> Dict[str, str]:
        """
        Convert an url into a dict of key/value for all the parameters of the url
        """
        output = {}
        # Split the path from the parameters
        splitted_url = url.split("?")
        # If there is no parameters return empty
        if len(splitted_url) != 2:
            return output
        # Split all the parameters and their variables and values
        parameters = splitted_url[1]
        for parameter in parameters.split("&"):
            splitted_parameter = parameter.split("=")
            if len(splitted_parameter) == 2:
                output[splitted_parameter[0]] = splitted_parameter[1]

        return output

    @staticmethod
    def parameters_to_url(base_url: str, parameters: Dict[str, str]) -> str:
        """
        Convert a dictionary of parameters to an url
        """
        output = base_url
        # If there is not parameters given just return the base url
        if len(parameters) < 1:
            return output

        # Concatenate all the parameters to te base url
        output += "?"
        for key, value in parameters.items():
            output += f"{key}={value}&"
        # Remove the dandeling '&'
        output = output[:-1]

        return output
