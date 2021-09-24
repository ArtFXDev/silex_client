from threading import Thread
from typing import Coroutine
from concurrent.futures import Future
import gc
import atexit
import asyncio
from contextlib import suppress

from silex_client.utils.log import logger

class EventLoop:
    """
    Class responsible to manage the async event loop, to deal with websocket
    connection, and action execution

    :ivar TASK_SLEEP_TIME: How long in second to wait for the thread to join before returning an error
    """

    JOIN_THREAD_TIMEOUT = 2

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.tasks = []
        self.thread = None
        atexit.register(self.stop)

    @property
    def is_running(self) -> bool:
        return self.loop.is_running()

    def _start_event_loop(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

        # Clear it once completed
        self._clear_event_loop()

    def _clear_event_loop(self) -> None:
        if self.is_running:
            logger.info("Could not clear the event loop: The loop must be stopped before being cleared")
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
            logger.warning("Could not start event loop: The loop is already running")
            return

        self._start_event_loop()

    def start_multithreaded(self) -> None:
        """
        initialize the event loop's task and run it in a different thread
        """
        if self.is_running:
            logger.warning("Could not start event loop: The loop is already running")
            return

        self.thread = Thread(target=self._start_event_loop)
        self.thread.start()

    def stop(self) -> None:
        """
        Ask to all the event loop's tasks to stop and join the thread to the main thread
        if there is one running
        """
        if not self.loop.is_running():
            return

        if self.thread is not None and self.thread.isAlive():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(self.JOIN_THREAD_TIMEOUT)
            if self.thread.isAlive:
                logger.error("Could not stop the event loop thread: timout exeded")
        else:
            self.loop.stop()

    def register_task(self, coroutine: Coroutine) -> Future:
        """
        Helper to add tasks to the event loop from a different thread

        The result value can be awaited with result = future.result(timeout)
        and the task can be canceled with future.cancel()
        """
        if not self.is_running:
            logger.warning("Could not register task %s: The event loop is not running", coroutine)
            future = Future()
            future.set_result(None)
            return future

        return asyncio.run_coroutine_threadsafe(coroutine, self.loop)
