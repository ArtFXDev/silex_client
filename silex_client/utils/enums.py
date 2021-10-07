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
    PROCESSING = 2
    INVALID = 3
    ERROR = 4
    WAITING_FOR_RESPONSE = 5
