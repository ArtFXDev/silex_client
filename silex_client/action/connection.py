"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of Connection
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.base_buffer import BaseBuffer


class Connection:
    """
    Represent a connection between two sockets
    It can be set to either the input or output field, so when the data
    will be queried, the output of the socket it leads to will be returned.

    In the yaml definition of an action, a connection can be created with the
    tag !connection plus the path to the socket you want. That path must be
    relative to the closest ActionBuffer parent.
    """

    SPLIT = "."

    def __init__(self, path: str):
        self.path = path.strip(self.SPLIT).split(self.SPLIT)

    @staticmethod
    def get_buffer(action_query: ActionQuery, path: List[str]) -> Tuple[BaseBuffer, List[str]]:
        """
        Get the buffer this connection is leading to by traversing the outputs
        If the given path leads to a dead end, the remaining path is returned

        Example:
            If a path ["foo", "bar", "john", "doe"] is given,
            but <bar> does not have a <john> children, this method will
            return <bar> as a result and ["john", "doe"] as a remaining path
        """
        remaining_path: List[str] = []
        buffer: BaseBuffer = action_query.buffer

        # Traverse recursively the children of the buffers
        for index, child_name in enumerate(path[1:]):
            child = buffer.children.get(child_name)
            if child is None:
                # The traversal stoped before going throug the full path
                # We must store the remaining part of the path we couldn't go trough
                remaining_path = path[index + 1 :]
                break
            buffer = child

        return buffer, remaining_path

    def resolve(self, action_query: ActionQuery, prefix: str = "") -> Any:
        """
        Get the output of the socket this connection leads to by recursively going throught
        the connections.
        """
        full_path = [*prefix.strip(self.SPLIT).split(self.SPLIT), *self.path]

        if len(full_path) < 2:
            logger.error(("Could not resolve the connection %s: ",
            "Please specify at least input/output and a key"), full_path)
            return None

        (*buffer_path, key, socket) = full_path
        buffer, remaining_path = self.get_buffer(action_query, buffer_path)

        if remaining_path:
            logger.error(("Could not resolve the connection %s: ",
                "the buffer %s has not %s child"), full_path, buffer.name, remaining_path[0])
            return None

        if socket == "input":
            if key not in buffer.inputs:
                logger.error(("Could not resolve the connection %s: ",
                    "the buffer %s has no input %s"), full_path, buffer.name, key)
                return None
            return buffer.eval_input(action_query, key)
        if socket == "output":
            if key not in buffer.outputs:
                logger.error(("Could not resolve the connection %s: ",
                    "the buffer %s has no output %s"), full_path, buffer.name, key)
                return None
            return buffer.eval_output(action_query, key)

        logger.error(("Could not resolve the connection %s: ",
            "Please specify input or output"), full_path)
        return None

    def __str__(self):
        return self.SPLIT.join(self.path)

    def __repr__(self):
        return f'Connection(path="{self.path}")'
