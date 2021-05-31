"""
@author: michael.haussmann
retake by le TD gang

A simple logger shortcut / wrapper.

Uses
https://logzero.readthedocs.io/

"""

import os
import sys
import logging
import logzero
from logzero import logger

__logFormat = '[SILEX]    [%(asctime)s] %(color)s%(levelname)-8s%(end_color)s| [%(module)s.%(funcName)s] %(color)s%(message)-80s%(end_color)s (%(lineno)d)'

handler = logging.StreamHandler(sys.stdout)  # stream to stdout for pycharm
handler.setFormatter(logzero.LogFormatter(fmt=__logFormat))
logger.handlers = []
logger.addHandler(handler)

log_level = getattr(logging, os.getenv("SILEX_LOG_LEVEL", "WARNING"))
logger.setLevel(log_level)  # set default level
