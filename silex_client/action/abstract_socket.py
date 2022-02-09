"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of AbstractSocketBuffer
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Union, TYPE_CHECKING

from silex_client.action.connection import Connection
from silex_client.utils.socket_types import SocketTypeMeta

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

# Alias the metaclass type, to avoid clash with the type attribute
TypeAlias = type


@dataclass()
class AbstractSocketBuffer(ABC):
    """
    Abstract class used for dependencie injection into the BaseBuffer class
    The SocketBuffer class, inherit from BaseBuffer and BaseBuffer has SocketBuffer fields.
    This class is here to solve the circular dependencie
    """

    #: The expected type in the output, the input will be casted in to this type
    type: Union[TypeAlias, SocketTypeMeta] = field(default=TypeAlias(None))
    #: Store the raw value passed in
    value: Any = field(default=None)
    #: Specify if the buffer must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)

    @abstractmethod
    def eval(self, action_query: ActionQuery) -> Any:
        """
        The output of a socket buffer is the result of the value casted to the desired type
        """

    @abstractmethod
    def resolve_connection(
        self, action_query: ActionQuery, connection: Connection
    ) -> Any:
        """
        Resolve connection of the given value
        """
