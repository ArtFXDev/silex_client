"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of AbstractSocketBuffer
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Union

from silex_client.utils.socket_types import SocketTypeMeta


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
    #: The input store the raw value passed in
    input: Any = field(default=None, init=False)
    #: The output store the cache of the casted value
    output: Any = field(default=None, init=False)
    #: Specify if the buffer must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)

    @abstractmethod
    def eval(self, action_query) -> Any:
        """
        The output of a socket buffer is the result of the input casted to the desired type
        """
