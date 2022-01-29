"""
@author: TD gang

Helpers to encode or decode the json stream
"""

import uuid

import fileseq
import jsondiff

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.parameter_types import ParameterInputTypeMeta


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

    # Use the serialize method for command parameters
    if isinstance(obj, ParameterInputTypeMeta):
        return obj.serialize()

    # Convert frameset to string
    if isinstance(obj, fileseq.FrameSet):
        return str(obj)

    # Convert types into string
    if isinstance(obj, type):
        return {"name": obj.__name__}

    return None


class CustomDiffSyntax(jsondiff.CompactJsonDiffSyntax):
    """
    Silex does not support any syntax for removing items from a dict
    or inserting items in a list.
    """

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
    """
    Differ that use the diff syntax overrides defined in CustomDiffSyntax
    """

    def __init__(self, marshal=False):
        super().__init__(marshal=marshal)
        self.options.syntax = CustomDiffSyntax()


def silex_diff(a_object, b_object, marshal=False):
    """
    Helper to make a diff with right configuration to make it json serializable
    """
    return jsondiff.diff(a_object, b_object, cls=CustomJsonDiffer, marshal=marshal)
