"""
@author: michael.haussmann
retake by le TD gang

A simple logger shortcut / wrapper.

Uses
https://logzero.readthedocs.io/

"""

import logging
import os
import sys
import tempfile

import logzero
from logzero import logger, setup_logger

# Formatting of the output log to look like
__LOG_FORMAT__ = "[SILEX] [%(asctime)s] %(color)s%(levelname)-5s%(end_color)s | [%(module)s.%(funcName)s] %(color)s%(message)-50s%(end_color)s (%(lineno)d)"

handler = logging.StreamHandler(sys.stdout)  # stream to stdout for pycharm
formatter = logzero.LogFormatter(fmt=__LOG_FORMAT__)
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)

env_log_level = os.getenv("SILEX_LOG_LEVEL", "DEBUG")
env_log_level = env_log_level.upper()
if env_log_level not in logging._nameToLevel:
    env_log_level = "DEBUG"
    logger.error("Invalid log level (%s): Setting DEBUG as value", env_log_level)

log_level = getattr(logging, env_log_level)
logger.setLevel(log_level)  # set default level

# File logger for dev and debug
__FILE_FORMAT__ = "[SILEX] [%(asctime)s] %(levelname)s | [%(module)s.%(funcName)s] %(message)-50s (%(lineno)d)"

log_path = f"{tempfile.gettempdir()}/silex_client_logs"  # under Windows look for %TEMP%\silex_client_logs

os.makedirs(log_path, exist_ok=True)
os.chmod(log_path, 0o0777)
formatter = logging.Formatter(__FILE_FORMAT__)
flog = setup_logger(
    name="flog",
    logfile=f"{log_path}/flog.log",
    level=logzero.DEBUG,
    formatter=formatter,
)
