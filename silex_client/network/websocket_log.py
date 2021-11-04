import logging

import logzero
import traceback

from silex_client.utils.log import formatter

# Formatting of the output log to look like
__LOG_FORMAT = "[SILEX]\
    [%(asctime)s] %(levelname)-10s|\
    [%(module)s.%(funcName)s] %(message)-50s (%(lineno)d)"
formatter = logzero.LogFormatter(fmt=__LOG_FORMAT)


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

        log = {"level": record.levelname, "message": formatter.format(record)}
        self.silex_command.logs.append(log)
        self.action_query.update_websocket()


class RedirectWebsocketLogs(object):
    def __init__(self, logger: logging.Logger, action_query, command):
        self.action_query = action_query
        self.silex_command = command
        self.logger = logger
        self.handler = WebsocketLogHandler(action_query, command)

    def __enter__(self):
        self.logger.addHandler(self.handler)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            exception = traceback.format_exception(exc_type, exc_value, exc_traceback)
            log = {"level": "TRACEBACK", "message": str(exception)}
            self.silex_command.logs.append(log)
            self.action_query.update_websocket()
        self.logger.handlers.remove(self.handler)
