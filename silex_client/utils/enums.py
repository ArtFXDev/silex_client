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


class ConflictBehaviour(IntEnum):
    """
    Used for file conflicts in copy, rename...
    """

    OVERRIDE = 0
    ALWAYS_OVERRIDE = 1
    KEEP_EXISTING = 2
    ALWAYS_KEEP_EXISTING = 3
    MERGE = 4
    ALWAYS_MERGE = 5
    RENAME = 6
    REPATH = 7


class NotFoundBehaviour(IntEnum):
    """
    Used when a file is not found
    """

    NEW_PATH = 0
    SKIP_FILE = 1
    SKIP_ALL = 2
