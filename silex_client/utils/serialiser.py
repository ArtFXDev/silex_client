"""
@author: TD gang

Helpers to encode or decode the json stream
"""

import uuid

import pathlib
import jsondiff
import fileseq

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

    # Convert ActionBuffer, CommandBuffer and command parameters into dict
    if isinstance(obj, (ActionBuffer, CommandBuffer, CommandParameterMeta)):
        return obj.serialize()

    # Convert frameset and pathlib to string
    if isinstance(obj, (fileseq.FrameSet, pathlib.Path)):
        return str(obj)

    # Convert types into string
    if isinstance(obj, type):
        return {"name": obj.__name__}


class CustomDiffSyntax(jsondiff.CompactJsonDiffSyntax):
    def emit_list_diff(self, a, b, s, inserted, changed, deleted):
        """
        Customise the diff of lists, just return the new list completly instead of
        separating the insert, changes, and deletions
        """
        return b

    def emit_dict_diff(self, a, b, s, added, changed, removed):
        """
        Customise the diff of dictionaries, don't specify when an entry is removed
        """
        if s == 0.0 or removed:
            return b
        if s == 1.0:
            return {}

        changed.update(added)
        return changed


class CustomJsonDiffer(jsondiff.JsonDiffer):
    def __init__(self, marshal=False):
        super().__init__(marshal=marshal)
        self.options.syntax = CustomDiffSyntax()

    def _list_diff(self, X, Y):
        return Y, 1.0


def silex_diff(a, b, marshal=False):
    """
    Helper to make a diff with right configuration to make it json serializable
    """
    return jsondiff.diff(a, b, cls=CustomJsonDiffer, marshal=marshal)
