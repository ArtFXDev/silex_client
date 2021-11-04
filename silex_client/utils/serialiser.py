"""
@author: TD gang

Helpers to encode or decode the json stream
"""

import uuid

import jsondiff

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.parameter_types import CommandParameterMeta


def silex_encoder(obj):
    """
    Helper to encode the action buffer to json
    """
    # Convert UUID into hex code
    if isinstance(obj, uuid.UUID):
        return obj.hex

    # Convert ActionBuffer into dict
    if isinstance(obj, ActionBuffer):
        return obj.serialize()

    # Convert ActionBuffer into dict
    if isinstance(obj, CommandBuffer):
        return obj.serialize()

    # Convert types into string
    if isinstance(obj, CommandParameterMeta):
        return obj.serialize()

    # Convert types into string
    if isinstance(obj, type):
        return {"name": obj.__name__}


class CustomDiffSyntax(jsondiff.CompactJsonDiffSyntax):
    def emit_list_diff(self, a, b, s, inserted, changed, deleted):
        return b


class CustomJsonDiffer(jsondiff.JsonDiffer):
    def __init__(self, marshal=False):
        super().__init__(marshal=marshal)
        self.options.syntax = CustomDiffSyntax()


def silex_diff(a, b, marshal=False):
    """
    Helper to make a diff with right configuration to make it json serializable
    """
    return jsondiff.diff(a, b, cls=CustomJsonDiffer, marshal=marshal)
