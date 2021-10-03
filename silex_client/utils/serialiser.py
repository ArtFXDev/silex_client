import uuid

from silex_client.action.action_buffer import ActionBuffer
from silex_client.action.command_buffer import CommandBuffer


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
