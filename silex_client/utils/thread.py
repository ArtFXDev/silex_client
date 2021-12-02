import asyncio
import threading
from typing import Callable

from silex_client.core.context import Context
from silex_client.utils.log import logger


async def execute_in_thread(function: Callable, *args, **kwargs):
    """
    Execute the given function in a different thread and wait for its result
    """

    future = Context.get().event_loop.loop.create_future()

    def wrapped_function():
        async def set_future_result(result):
            future.set_result(result)

        async def set_future_exception(exception):
            future.set_exception(exception)

        try:
            result = function(*args, **kwargs)
            Context.get().event_loop.register_task(set_future_result(result))
        except Exception as ex:
            Context.get().event_loop.register_task(set_future_exception(ex))

    thread = threading.Thread(target=wrapped_function, daemon=True)
    thread.start()

    def callback(task_result: asyncio.Future):
        if task_result.cancelled():
            return

        exception = task_result.exception()
        if exception:
            logger.error("Exception raised in wrapped execute call: %s", exception)
            raise Exception(f"Exception raised in wrapped execute call: {exception}")

    future.add_done_callback(callback)
    return await future
