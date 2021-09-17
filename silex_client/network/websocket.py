"""
@author: TD gang
Class definition that connect the the given url throught websockets,
receive and handle the incomming messages
"""

import asyncio
import copy
import gc
from contextlib import suppress
from threading import Thread
from typing import Union

import socketio
from silex_client.utils.log import logger


class WebsocketConnection:
    """
    Websocket client that connect the the given url
    and receive and handle the incomming messages

    :ivar TASK_SLEEP_TIME: How long in second to wait between each update loop
    """

    # Defines how long each task will wait between every loop
    TASK_SLEEP_TIME = 0.5

    def __init__(self, url: str = None):
        self.is_running = False
        self.pending_stop = False
        self.pending_transmissions = []

        self.socketio = socketio.AsyncClient()
        self.loop = asyncio.new_event_loop()
        self.thread = None

        # Set the url accordingly
        if url is None:
            url = "http://localhost:8080"
        self.url = url

        # Define the event handlers
        @self.socketio.on("connect")
        async def on_connect():
            logger.info("Connected to %s established", self.url)

        @self.socketio.on("connect_error")
        async def on_connect_error(data):
            logger.error("Connection to %s failed", self.url)

        @self.socketio.on("disconnect")
        async def on_disconnect():
            logger.info("Disconected from %s", self.url)
        
        @self.socketio.on("message")
        async def on_message(data):
            logger.debug("Received message %s from %s", data, self.url)

    def __del__(self):
        if self.is_running:
            self.stop()

    async def _listen_socketio(self) -> None:
        await self.socketio.connect(self.url)
        while True:
            # Sleep a bit between each iteration
            await asyncio.sleep(self.TASK_SLEEP_TIME)
            # Exit the loop if a stop has been asked
            if self.pending_stop:
                await self.socketio.disconnect()
                break

    async def _emmit_socketio(self) -> None:
        while True:
            # Sleep a bit between each iteration
            await asyncio.sleep(self.TASK_SLEEP_TIME)
            # Exit the loop if a stop has been asked
            if self.pending_stop:
                break
            if not self.socketio.connected:
                continue

            # Sleep a bit between each iteration
            await asyncio.sleep(1)
            # Move the pending_transmissions to a queue so we keep receiving
            # event while executing them
            transmission_queue = copy.deepcopy(self.pending_transmissions)
            self.pending_transmissions.clear()
            for message in transmission_queue:
                logger.debug("Websocket client sending %s", message)
                await self.socketio.emit('message', message)

    def _start_event_loop(self) -> None:
        if self.loop.is_running():
            logger.info("Event loop already running")
            return

        self.pending_stop = False
        asyncio.set_event_loop(self.loop)
        socketio_connection = self.loop.create_task(self._listen_socketio())
        self.loop.create_task(self._emmit_socketio())
        try:
            self.loop.run_until_complete(socketio_connection)
        except KeyboardInterrupt:
            self.stop()

        # Stop the event loop and clear it once completed
        self.loop.call_soon_threadsafe(self.loop.stop)
        self._clear_event_loop()

    def _clear_event_loop(self) -> None:
        if self.loop.is_running():
            logger.info("The event loop must be stopped before being cleared")
            return

        logger.info("Clearing event loop...")
        # Clear the loop
        for task in asyncio.all_tasks(self.loop):
            # The cancel method will raise CancelledError on the running task to stop it
            task.cancel()
            # Wait for the task's cancellation in a suppress context to mute the CancelledError
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(task)

        # Create a new loop and let the old one get garbage collected
        self.loop = asyncio.new_event_loop()
        # Trigger the garbage collection
        gc.collect()

        logger.info("Event loop cleared")

    def start(self) -> None:
        """
        initialize the event loop's task and run it in main thread
        """
        if self.is_running:
            logger.warning("Websocket server already running")
            return

        self.is_running = True
        self._start_event_loop()

    def start_multithreaded(self) -> None:
        """
        initialize the event loop's task and run it in a different thread
        """
        if self.is_running or self.thread is not None:
            logger.warning("Websocket server already running")
            return

        self.is_running = True
        self.thread = Thread(target=self._start_event_loop)
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
            self.thread.join(1)
            if self.thread.is_alive():
                logger.warning("Could not stop the websocket connection thread for %s",
                               self.url)
            else:
                self.thread = None
        self.is_running = False

    def send(self, message: Union[str, list, dict, tuple]) -> None:
        """
        Add the given message to the list of pending message to be sent
        """
        self.pending_transmissions.append(message)

    @staticmethod
    def url_to_parameters(url: str) -> dict:
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
    def parameters_to_url(base_url: str, parameters: dict) -> str:
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
