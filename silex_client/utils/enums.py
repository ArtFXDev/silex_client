from enum import IntEnum


class Status(IntEnum):
    """
    Used by action/command buffers to communicate their state to the UI
    """

    COMPLETED = 0
    PROCESSING = 1
    INITIALIZED = 2
    INVALID = 3
    ERROR = 4
