from threading import Thread
import asyncio
from contextlib import suppress

from silex_client.utils.log import logger

class EventLoop:
    """
    Class responsible to manage the async event loop, to deal with websocket
    connection, and action execution
    """

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.tasks = []
        self.thread = None

    def _start_event_loop(self) -> None:
        if self.loop.is_running():
            logger.info("Event loop already running")
            return

        self.pending_stop = False
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

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
