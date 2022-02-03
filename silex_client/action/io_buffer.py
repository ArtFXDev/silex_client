"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union, TYPE_CHECKING

from silex_client.action.connection import Connection
from silex_client.action.base_buffer import BaseBuffer
from silex_client.utils.io_types import AnyType, IOTypeMeta

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

# Alias the metaclass type, to avoid clash with the type attribute
TypeAlias = type


@dataclass()
class IOBuffer(BaseBuffer):
    """
    Store the data of an input or output of an other buffer.
    This buffer is responsible to cast the input values into the desired type, and
    then cache the result in the output.
    """

    PRIVATE_FIELDS = ["outdated_cache", "serialize_cache", "parent", "output"]
    READONLY_FIELDS = ["type", "label"]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="io")
    #: The type of the io, must be a class definition or a BufferIOMeta instance
    type: Union[TypeAlias, IOTypeMeta] = field(default=TypeAlias(None))
    #: The input store the raw value passed in
    input: Any = field(default=None, init=False)
    #: The output store the cache of the casted value
    output: Any = field(default=None, init=False)

    def __post_init__(self):
        super().__post_init__()
        # The AnyParameter type does not have any widget in the frontend
        if self.type is AnyType:
            self.hide = True

        # Get the default value from to the type
        if self.input is None and isinstance(self.type, IOTypeMeta):
            self.input = self.type.get_default()

    def rebuild_type(self, *args, **kwargs):
        """
        Allows changing the options of the parameter by rebuilding the type
        """
        if not isinstance(self.type, IOTypeMeta):
            return

        # Rebuild the parameter type
        self.type = self.type.rebuild(*args, **kwargs)

        if self.input is None:
            self.input = self.type.get_default()

    def get_input(self, action_query: ActionQuery, *args, **kwargs) -> Any:
        """
        The input of an IO buffer can be a Connetion or anything
        """
        if isinstance(self.input, Connection):
            return self.resolve_io(action_query, self.input)
        return self.input

    def get_output(self, action_query: ActionQuery, *args, **kwargs) -> Any:
        """
        The output of an IO buffer is the result of the input casted to the desired type
        """
        return self.type(self.get_input(action_query))


@dataclass()
class InputBuffer(IOBuffer):

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="input")


@dataclass()
class OutputBuffer(IOBuffer):

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="output")
