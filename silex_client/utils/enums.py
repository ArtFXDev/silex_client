"""
@author: TD gang

Set of enums that are used across the silex repo
"""

from enum import IntEnum


class Status(IntEnum):
    """
    Used by action/command buffers to communicate their state to the UI
    """

    COMPLETED = 0
    INITIALIZED = 1
    WAITING_FOR_RESPONSE = 2
    PROCESSING = 3
    INVALID = 4
    ERROR = 5


class Execution(IntEnum):
    """
    Used by actions to set the type of execution
    """

    PAUSE = 0
    FORWARD = 1
    BACKWARD = 2
