from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from silex_client.graph.graph_item import GraphItem
from silex_client.socket_types.socket_type import SocketType
from silex_client.socket_types.void_socket import VoidSocket


@dataclass()
class Socket(GraphItem):
    """
    Store the data of an input or output of an other buffer.
    This buffer is responsible to hold and cast the input values into the desired type
    """

    #: The expected type in the output, the input will be casted in to this type
    type: SocketType = field(default_factory=VoidSocket)

    #: The raw input that will be casted into the desired type for the output
    value: Any = field(default=None)

    def eval(self) -> Any:
        """
        Compute output value of the socket by resolving connections and casting to the
        expected type.
        """
