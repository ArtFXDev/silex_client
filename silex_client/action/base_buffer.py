"""
@author: TD gang

Dataclass that all the buffers of a command must inherit from
"""

from __future__ import annotations

import copy
import re
import uuid as unique_id
from dataclasses import dataclass, field, fields
from functools import partial
from typing import (Any, Dict, List, Optional, Tuple, Type, TypeVar, Union,
                    get_type_hints)

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff
from dacite.types import is_union

from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Status

TBaseBuffer = TypeVar("TBaseBuffer", bound="BaseBuffer")


@dataclass()
class BaseBuffer:
    """
    Store the data of a buffer, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = [
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["label"]

    #: Specify if the childs can be hidden or not
    ALLOW_HIDE_CHILDS = True

    #: Name of the buffer, must have no space or special characters
    name: str = field(default="unnamed")
    #: The name of the buffer, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: Parents in the buffer hierarchy of buffer of the action
    parent: Optional[BaseBuffer] = field(repr=False, default=None)
    #: Childs in the buffer hierarchy of buffer of the action
    children: Dict[str, BaseBuffer] = field(default_factory=dict)
    #: Specify if the buffer must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: Optional[str] = field(compare=False, repr=False, default=None)
    #: A Unique ID to help differentiate multiple buffers
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))
    #: Marquer to know if the serialize cache is outdated or not
    outdated_cache: bool = field(compare=False, repr=False, default=True)
    #: Cache the serialize output
    serialize_cache: dict = field(compare=False, repr=False, default_factory=dict)
    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="none")

    def __setattr__(self, name, value):
        super().__setattr__("outdated_cache", True)
        super().__setattr__(name, value)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

    @classmethod
    def get_child_types(cls) -> Tuple[Type[BaseBuffer]]:
        """
        The childs type are to possible class that this buffer can have in the children field
        """
        children_type = get_type_hints(cls)["children"].__args__[1]
        if is_union(children_type):
            return children_type.__args__
        return (children_type,)

    @property
    def outdated_caches(self) -> bool:
        """
        Check if the cache need to be recomputed by looking at the current cache
        and the children caches
        """
        return self.outdated_cache or not all(
            not child.outdated_caches for child in self.children.values()
        )

    def get_path(self) -> str:
        """
        Traverse the parent tree to get the path that lead to this buffer
        """
        path = ""
        parent: Optional[BaseBuffer] = self

        while parent is not None:
            path = f"{parent.name}:{path}" if path else parent.name
            parent = parent.parent

        return path

    def serialize(self, ignore_fields: List[str] = None) -> Dict[str, Any]:
        """
        Convert the buffer's data into json so it can be sent to the UI
        """
        if not self.outdated_caches:
            return self.serialize_cache

        if ignore_fields is None:
            ignore_fields = self.PRIVATE_FIELDS

        result = []

        for buffer_field in fields(self):
            if buffer_field.name in ignore_fields:
                continue
            if buffer_field.name == "children":
                children = getattr(self, buffer_field.name)
                children_value = {}
                for child_name, child in children.items():
                    if self.ALLOW_HIDE_CHILDS and child.hide:
                        continue
                    children_value.setdefault(child.buffer_type, {})
                    children_value[child.buffer_type][child_name] = child.serialize()
                for child_type in self.get_child_types():
                    buffer_type = child_type.buffer_type
                    result.append((buffer_type, children_value.get(buffer_type, {})))
                continue

            result.append((buffer_field.name, getattr(self, buffer_field.name)))

        self.serialize_cache = copy.deepcopy(dict(result))
        self.outdated_cache = False
        return self.serialize_cache

    def _deserialize_child(
        self, expected_child_type: Type[BaseBuffer], child_data: Any
    ) -> BaseBuffer:
        """
        Called bu deserialize to deserialize a given child of this buffer
        """
        child_name = child_data.get("name")
        child = self.children.get(child_name)

        # If the given child is a new child we construct it
        if child is None:
            for child_type in self.get_child_types():
                if child_data.get("buffer_type") == child_type.buffer_type:
                    if expected_child_type is not child_type:
                        raise Exception("The given expected child type is invalid")
                    return child_type.construct(child_data, self)
            raise TypeError(
                f"Could not deserialize the buffer {child_name}, the buffer_type is invalid"
            )

        # Otherwise, we update the already existing one
        child.deserialize(child_data)
        return child

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        """
        Reconstruct this buffer from the given serialized data
        """
        # Don't take the modifications of the hidden commands
        if self.hide and not force:
            return

        # Patch the current buffer's data, except the children data
        current_buffer_data = self.serialize()
        for child_type in self.get_child_types():
            current_buffer_data.pop(child_type.buffer_type, None)
        serialized_data = jsondiff.patch(current_buffer_data, serialized_data)

        # Format the children corectly, the name is defined in the key only
        children_data = [
            (name, data, child_type)
            for child_type in self.get_child_types()
            for name, data in serialized_data.get(child_type.buffer_type, {}).items()
        ]
        for child_name, child, child_type in children_data:
            child["name"] = child_name
            child["buffer_type"] = child_type.buffer_type

        # Create a new buffer with the patched serialized data
        config_data: Dict[str, Union[list, dict]] = {"cast": [Status, CommandOutput]}
        if BaseBuffer not in self.get_child_types():
            config_data["type_hooks"] = {
                child_type: partial(self._deserialize_child, child_type)
                for child_type in self.get_child_types()
            }
        config = dacite_config.Config(**config_data)

        for child_type in self.get_child_types():
            buffer_type = child_type.buffer_type
            if buffer_type not in serialized_data:
                continue
            serialized_data.setdefault("children", {})
            serialized_data["children"].update(serialized_data.pop(buffer_type))

        new_buffer = dacite.from_dict(type(self), serialized_data, config)

        # Keep the current value for the private and readonly fields
        for private_field in self.PRIVATE_FIELDS + self.READONLY_FIELDS:
            setattr(new_buffer, private_field, getattr(self, private_field))

        # Update the current fields value with the new buffer's values
        self.children.update(new_buffer.children)
        new_buffer_data = new_buffer.__dict__
        del new_buffer_data["children"]
        self.__dict__.update(new_buffer_data)

        self.outdated_cache = True

    @classmethod
    def construct(
        cls: Type[TBaseBuffer],
        serialized_data: Dict[str, Any],
        parent: BaseBuffer = None,
    ) -> TBaseBuffer:
        """
        Create an command buffer from serialized data

        The difference with deserialize and construct is that construct is used
        when the buffer is newly created, instead of updated
        """
        config = dacite_config.Config(cast=[Status, CommandOutput])

        # Initialize the buffer without the children,
        # because the children needs special treatment
        filtered_data = copy.copy(serialized_data)
        filtered_data["parent"] = parent
        for child_type in cls.get_child_types():
            filtered_data.pop(child_type.buffer_type, None)
        buffer = dacite.from_dict(cls, filtered_data, config)

        # Deserialize the newly created buffer to apply the children
        buffer.deserialize(serialized_data, force=True)
        return buffer
