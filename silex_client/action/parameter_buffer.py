"""
@author: TD gang

Dataclass used to store the data related to a parameter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Type, Union, TYPE_CHECKING, Dict

from silex_client.action.base_buffer import BaseBuffer
from silex_client.utils.parameter_types import AnyParameter, ParameterInputTypeMeta

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
    READONLY_FIELDS = ["value_type", "label"]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="parameters")
    #: The type of the parameter, must be a class definition or a CommandParameterMeta instance
    value_type: Union[Type, ParameterInputTypeMeta] = field(default=type(None))

    def __post_init__(self):
        super().__post_init__()
        # The AnyParameter type does not have any widget in the frontend
        if self.value_type is AnyParameter:
            self.hide = True

        # Get the default value from to the type
        if self.input is None and isinstance(self.value_type, ParameterInputTypeMeta):
            self.input = self.value_type.get_default()

    def rebuild_type(self, *args, **kwargs):
        """
        Allows changing the options of the parameter by rebuilding the type
        """
        if not isinstance(self.value_type, ParameterInputTypeMeta):
            return

        # Rebuild the parameter type
        self.value_type = self.value_type.rebuild(*args, **kwargs)

        if self.input is None:
            self.input = self.value_type.get_default()

    @property
    def outdated_caches(self) -> bool:
        """
        Check if the cache need to be recomputed by looking at the current cache
        and the children caches
        """
        return self.outdated_cache

    def get_output(self, action_query: ActionQuery) -> Any:
        """
        Always use this method to get the output of the buffer
        Return the output after resolving connections
        """
        return self.value_type(self._resolve_io(action_query, self.input))

    @classmethod
    def construct(
        cls,
        serialized_data: Dict[str, Any],
        parent: BaseBuffer = None,
    ) -> ParameterBuffer:
        # "value" can be used as a shortcut to set the input
        if "value" in serialized_data and "input" not in serialized_data:
            serialized_data["input"] = serialized_data.pop("value")
        # "type" can be used as a shortcut to set the value_type
        if "type" in serialized_data and "value_type" not in serialized_data:
            serialized_data["value_type"] = serialized_data.pop("type")
        return super().construct(serialized_data, parent)
