from enum import IntEnum


class Status(IntEnum):
    COMPLETED = 0
    PROCESSING = 1
    INITIALIZED = 2
    INVALID = 3
    ERROR = 4
