import logging

import asyncio
import os
import logzero
import traceback
from concurrent import futures

from silex_client.utils.log import formatter
from silex_client.utils.enums import Status

# Formatting of the output log to look like
__LOG_FORMAT__ = "[SILEX]\
    [%(asctime)s] %(levelname)-10s|\
    [%(module)s.%(funcName)s] %(message)-50s (%(lineno)d)"
websocket_formatter = logzero.LogFormatter(fmt=__LOG_FORMAT__)


class WebsocketLogHandler(logging.Handler):
    """
    Handler to send all the logs to the given namespace and event through websocket
    """

    def __init__(self, action_query, command):
        self.action_query = action_query
        self.silex_command = command
        super().__init__()

    def emit(self, record):
        """
        Capture the record and append it to the action logs
        """
        if record.levelname == "DEBUG":
            return

        log = {"level": record.levelname, "message": websocket_formatter.format(record)}
        self.silex_command.logs.append(log)
        self.silex_command.outdated_cache = True
        self.action_query.update_websocket()


class RedirectWebsocketLogs(object):
    def __init__(self, action_query, command):
        self.action_query = action_query
        self.silex_command = command
        self.logger = logzero.setup_logger(
            name=command.uuid,
            level=os.getenv("SILEX_LOG_LEVEL", "DEBUG"),
            formatter=formatter,
        )
        self.handler = WebsocketLogHandler(action_query, command)

    async def __aenter__(self) -> logging.Logger:
        self.logger.addHandler(self.handler)
        return self.logger

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        if exc_type and not (
            exc_type == futures.CancelledError or exc_type == asyncio.CancelledError
        ):
            self.logger.error(
                "An error occured while executing the command %s: %s",
                self.silex_command.name,
                exc_value,
            )
            self.silex_command.status = Status.ERROR

            traceback.print_tb(exc_traceback)
            exception = traceback.format_exception(exc_type, exc_value, exc_traceback)
            exception = "\n".join(exception)
            log = {"level": "TRACEBACK", "message": str(exception)}
            self.silex_command.logs.append(log)
            self.silex_command.outdated_cache = True
            await self.action_query.async_update_websocket()

        self.logger.handlers.remove(self.handler)
        return True
