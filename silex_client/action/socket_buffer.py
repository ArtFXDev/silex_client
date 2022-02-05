"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of SocketBuffer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from silex_client.action.base_buffer import BaseBuffer

from silex_client.action.connection import Connection
from silex_client.action.abstract_socket import AbstractSocketBuffer
from silex_client.utils.socket_types import AnyType, SocketTypeMeta

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


@dataclass()
class SocketBuffer(BaseBuffer, AbstractSocketBuffer):
    """
    Store the data of an input or output of an other buffer.
    This buffer is responsible to cast the input values into the desired type, and
    then cache the result in the output.
    """

    PRIVATE_FIELDS = [
        "parent",
        "outdated_cache",
        "serialize_cache",
        "inputs",
        "outputs",
        "output",
        "children",
        "buffer_type",
    ]
    READONLY_FIELDS = ["type", "buffer_type"]

    #: Type name to help differentiate the different buffer types
    buffer_type: None = field(default=None)

    def __post_init__(self):
        super().__post_init__()

        # The AnyType type does not have any widget in the frontend
        if self.type is AnyType:
            self.hide = True

        # Get the default value from to the type
        if self.input is None and isinstance(self.type, SocketTypeMeta):
            self.input = self.type.get_default()

        # Sockets buffers cannot have children
        self.children = {}

    def rebuild_type(self, *args, **kwargs):
        """
        Allows changing the options of the parameter by rebuilding the type
        """
        if not isinstance(self.type, SocketTypeMeta):
            return

        # Rebuild the socket type
        self.type = self.type.rebuild(*args, **kwargs)

        if self.input is None:
            self.input = self.type.get_default()

    def resolve_connection(self, action_query: ActionQuery, connection: Connection) -> Any:
        """
        Resolve connection of the given value
        """
        parent_action = self.get_parent(buffer_type="actions")
        prefix = ""
        if parent_action is not None:
            prefix = parent_action.get_path()
        return connection.resolve(action_query, prefix)

    def eval(self, action_query: ActionQuery) -> Any:
        """
        The output of a socket buffer is the result of the input casted to the desired type
        """
        raw_input = self.input
        if isinstance(raw_input, Connection):
            raw_input = self.resolve_connection(action_query, raw_input)

        return self.type(raw_input)

    def is_connected(self) -> bool:
        """
        Helper to know if the input is linked to an other SocketBuffer
        """
        return isinstance(self.input, Connection)
