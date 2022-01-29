"""
@author: TD gang

Class definition that represent a connection between a buffer output to a buffer input
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Tuple

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.base_buffer import BaseBuffer


class Connection:
    """
    Represent a connection between a buffer input and a buffer output.
    It can be set to either the data_in or data_out field, so when the data
    will be queried, the output of the buffer it leads to will be returned.

    The given path needs to be relative to the closest ActionBuffer parent we can't
    connect two buffers that don't have the same ActionBuffer parent
    """

    SPLIT = "."

    def __init__(self, path: str):
        self.path = path.strip(self.SPLIT)

    def get_buffer(
        self, action_query: ActionQuery, prefix: str = ""
    ) -> Tuple[BaseBuffer, str]:
        """
        Get the buffer this connection is leading to by traversing the children
        If the path is too long, the part of the path that has not been traversed is returned
        """
        # Add the path prefix to the original path
        path_prefix = prefix.strip(self.SPLIT)
        full_path = self.SPLIT.join([path_prefix, self.path]).split(self.SPLIT)

        path_left: List[str] = []
        buffer: BaseBuffer = action_query.buffer
        # Traverse recursively the children of the buffers
        for index, path in enumerate(full_path):
            child = buffer.children.get(path)
            if child is None:
                # The traversal stoped before going throug the full path
                # We must store the part of the path we didn't go trough to traverse the dict
                path_left = full_path[index:]
                break
            buffer = child

        return buffer, self.SPLIT.join(path_left)

    def get_output(self, action_query: ActionQuery, prefix: str = "") -> Any:
        """
        Get the output of the buffer this connection leads to by recursively going throught
        the children. This also go recursively throught items of a dict if the output
        of the buffer is a dictionary
        """
        buffer, path_left = self.get_buffer(action_query, prefix)
        buffer_output = buffer.get_output(action_query)

        # If we traversed the entire path, return the result directly
        if not path_left:
            return buffer_output

        # Traverse the returned dict with the left path
        for path in path_left:
            if not isinstance(buffer_output, dict):
                return buffer_output
            buffer_output = buffer_output.get(path)

        return buffer_output
