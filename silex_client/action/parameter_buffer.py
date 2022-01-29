"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, Union

from silex_client.action.base_buffer import BaseBuffer
from silex_client.utils.parameter_types import AnyParameter, ParameterInputTypeMeta

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
    input_type: Union[Type, ParameterInputTypeMeta] = field(default=type(None))
    #: The value that will return the parameter
    value: Any = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        # The AnyParameter type does not have any widget in the frontend
        if self.input_type is AnyParameter:
            self.hide = True

        # Get the default value from to the type
        if self.value is None and isinstance(self.input_type, ParameterInputTypeMeta):
            self.value = self.input_type.get_default()

    def rebuild_type(self, *args, **kwargs):
        """
        Allows changing the value of the parameter by rebuilding the type
        """
        if not isinstance(self.input_type, ParameterInputTypeMeta):
            return

        # Rebuild the parameter type
        self.input_type = self.input_type.rebuild(*args, **kwargs)

        if self.value is None:
            self.value = self.input_type.get_default()

    @property
    def outdated_caches(self) -> bool:
        """
        Check if the cache need to be recomputed by looking at the current cache
        and the children caches
        """
        return self.outdated_cache
