"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type, Optional

from silex_client.action.base_buffer import BaseBuffer
from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.parameter_types import AnyParameter, CommandParameterMeta

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

# Alias the metaclass type, to avoid clash with the type attribute
Type = type


@dataclass()
class ParameterBuffer(BaseBuffer):
    """
    Store the data of a parameter, it is used as a comunication payload with the UI
    """

    PRIVATE_FIELDS = ["outdated_cache", "serialize_cache", "parent"]
    READONLY_FIELDS = ["type", "label"]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="parameters")
    #: The type of the parameter, must be a class definition or a CommandParameterMeta instance
    type: Type = field(default=type(None))
    #: The value that will return the parameter
    value: Any = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        # The AnyParameter type does not have any widget in the frontend
        if self.type is AnyParameter:
            self.hide = True

        # Get the default value from to the type
        if self.value is None and isinstance(self.type, CommandParameterMeta):
            self.value = self.type.get_default()

    def rebuild_type(self, *args, **kwargs):
        """
        Allows changing the value of the parameter by rebuilding the type
        """
        if not isinstance(self.type, CommandParameterMeta):
            return

        # Rebuild the parameter type
        self.type = self.type.rebuild(*args, **kwargs)

        if self.value is None:
            self.value = self.type.get_default()

    @property
    def outdated_caches(self) -> bool:
        """
        Check if the cache need to be recomputed by looking at the current cache
        and the children caches
        """
        return self.outdated_cache

    def get_value(self, action_query: ActionQuery) -> Any:
        """
        Get the value of the parameter, always use this method to get
        the value of a parameter, this will resolve references, callable...
        """
        # If the value is the output of an other command, get is
        if isinstance(self.value, CommandOutput):
            return self.value.get_value(action_query)

        # If the value is a callable, call it (for mutable default values)
        if callable(self.value):
            return self.value()

        return self.value

    def get_path(self) -> str:
        """
        Traverse the parent tree to get the path that lead to this parameter
        """
        path = ""
        parent: Optional[BaseBuffer] = self

        while parent is not None:
            path = f"{parent.name}:{path}" if path else parent.name
            parent = parent.parent

        return path
