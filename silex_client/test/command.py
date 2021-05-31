"""
Test commands
"""

from silex_client.utils.log import logger


def empty():
    """
    Dummy function that does nothing
    """
    pass


def log(string="testing"):
    """
    Simple logger that just print
    """
    logger.info(string)
