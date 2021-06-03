"""
Test commands
"""

from silex_client.utils.log import logger


def empty():
    """
    Dummy function that does nothing
    """
    logger.info("testing test.command.empty")


def log(string="testing test.command.log"):
    """
    Simple logger that just print
    """
    logger.info(string)
