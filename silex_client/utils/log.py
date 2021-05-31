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

__logFormat = '[%(asctime)s] %(levelname)-8s| %(color)s[%(module)s.%(funcName)s] %(message)-80s (%(lineno)d)%(end_color)s'

handler = logging.StreamHandler(sys.stdout)  # stream to stdout for pycharm
handler.setFormatter(logzero.LogFormatter(fmt=__logFormat))
logger.handlers = []
logger.addHandler(handler)

log_level = getattr(logging, os.getenv("SILEX_LOG_LEVEL", "WARNING"))
logger.setLevel(log_level)  # set default level
