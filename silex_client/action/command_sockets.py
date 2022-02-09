"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of CommandSockets
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Union, Tuple, TypeVar

from silex_client.action.connection import Connection

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.action.abstract_socket import AbstractSocketBuffer

GenericType = TypeVar("GenericType")


class CommandSockets:
    """
    Helper to get and set the input/output values of a command quickly.
    Act like a dictionary
    """

    def __init__(
        self,
        action_query: ActionQuery,
        command: CommandBuffer,
        data: Dict[str, AbstractSocketBuffer],
    ):
        self.action_query = action_query
        self.command = command
        self.data = data

    def __getitem__(self, key: str):
        return self.data[key].eval(self.action_query)

    def __setitem__(self, key: str, value: Any):
        self.data[key].value = value

    def get(self, key: str, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value.
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default
        return self.__getitem__(key)

    def get_raw(self, key, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value without casting it to the expected type
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default

        raw_value = self.data[key].value
        if isinstance(raw_value, Connection):
            return self.data[key].resolve_connection(self.action_query, raw_value)

        return raw_value

    def get_buffer(self, key) -> AbstractSocketBuffer:
        """
        Return the socket buffer directly
        """
        return self.data[key]

    def keys(self) -> List[str]:
        """Same method a the original dict"""
        return list(self.data.keys())

    def values(self) -> List[Any]:
        """Same method a the original dict"""
        return [child.eval(self.action_query) for child in self.data.values()]

    def items(self) -> List[Tuple[str, Any]]:
        """Same method a the original dict"""
        return [
            (key, value.eval(self.action_query)) for key, value in self.data.items()
        ]

    def update(self, values: Union[CommandSockets, Dict[str, Any]]):
        """Update the values with the given dict"""
        for key, value in values.items():
            self[key] = value
