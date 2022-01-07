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

import logzero
from logzero import logger

# Formatting of the output log to look like
__LOG_FORMAT__ = "[SILEX]\
    [%(asctime)s] %(color)s%(levelname)-10s%(end_color)s|\
    [%(module)s.%(funcName)s] %(color)s%(message)-50s%(end_color)s (%(lineno)d)"

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
