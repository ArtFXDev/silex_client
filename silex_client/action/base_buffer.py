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
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_type_hints,
)

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff
from dacite.types import is_union

from silex_client.action.connection import Connection
from silex_client.utils.enums import Status
from silex_client.utils.log import logger

if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

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
        "data_in",
        "data_out",
    ]
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["label"]

    #: Specify if the childs can be hidden or not
    ALLOW_HIDE_CHILDS = True

    #: Name of the buffer, must have no space or special characters
    name: str = field(default="unnamed")
    #: The name of the buffer, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: The index of the buffer, to set the order in which they should be executed
    index: int = field(default=0)
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
    #: The input can be connected to an other buffer output
    data_in: Any = field(default=None, init=False)
    #: The output can be connected to an other buffer input
    data_out: Any = field(default=None, init=False)
    #: Marquer to know if the serialize cache is outdated or not
    outdated_cache: bool = field(compare=False, repr=False, default=True)
    #: Cache the serialize output
    serialize_cache: dict = field(compare=False, repr=False, default_factory=dict)
    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="none")
    #: Defines if the buffer must be executed or not
    skip: bool = field(default=False)

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
        The childs type are the possible classes that this buffer can have as children
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

    def get_child(
        self, child_path: List[str], child_type: Type[TBaseBuffer]
    ) -> Optional[TBaseBuffer]:
        """
        Helper to get a child that belong to this action from a path
        The data is quite nested, this is just for conveniance
        """
        if not child_path:
            logger.error("Could not get the child %s: Invalid path", child_path)
            return None

        child = self
        for key in child_path:
            if not isinstance(child, BaseBuffer):
                logger.error(
                    "Could not get the child %s: Invalid path",
                    child_path,
                )
                return None
            child = child.children.get(key)

        if not isinstance(child, child_type):
            logger.error(
                "Could not get the child %s: %s is not of type %s",
                child_path,
                child,
                child_type,
            )
            return None

        return child

    def get_parent(self, buffer_type: str) -> Optional[BaseBuffer]:
        """
        Get the first parent that has the given buffer type
        """
        parent: Optional[BaseBuffer] = self

        while parent is not None and not parent.buffer_type == buffer_type:
            parent = parent.parent

        if parent is None or parent.buffer_type != buffer_type:
            logger.error(
                "Could not get the parent of %s: %s is not of type %s",
                self,
                parent,
                buffer_type,
            )
            return None
        return parent

    def reorder_children(self):
        """
        Place the childrens in the right order accoring to the index value
        """
        self.children = dict(
            sorted(self.children.items(), key=lambda item: item[1].index)
        )

    def _resolve_data_in_out(self, action_query: ActionQuery, data: Any) -> Any:
        """
        Resolve connection of the given value
        """
        if not isinstance(data, Connection):
            return data

        parent_action = self.get_parent(buffer_type="actions")
        prefix = ""
        if parent_action is not None:
            prefix = parent_action.get_path()
        return data.get_output(action_query, prefix)

    def get_input(self, action_query: ActionQuery) -> Any:
        """
        Always use this method to get the intput of the buffer
        Return the input after resolving connections
        """
        return self._resolve_data_in_out(action_query, self.data_in)

    def get_output(self, action_query: ActionQuery) -> Any:
        """
        Always use this method to get the output of the buffer
        Return the output after resolving connections
        """
        return self._resolve_data_in_out(action_query, self.data_out)

    def skip_execution(self) -> bool:
        """
        Check if the current buffer or one of its parent is set to skip
        """
        parent: Optional[BaseBuffer] = self

        while parent is not None:
            if parent.skip:
                return True
            parent = parent.parent

        return False

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
                    children_value[child_name] = child.serialize()
                result.append(("children", children_value))
                continue

            result.append((buffer_field.name, getattr(self, buffer_field.name)))

        self.serialize_cache = copy.deepcopy(dict(result))
        self.outdated_cache = False
        return self.serialize_cache

    def _deserialize_child(
        self, expected_child_type: Type[BaseBuffer], child_data: Any
    ) -> BaseBuffer:
        """
        When deserialize is called, this method is used to cast the children
        in the desired buffer type

        WARNING: This method is called as a type_hooks by dacite, dacite
        is calling it in a broad try/except block, there is nothing to do about it,
        so every error in this function will be a silent error
        """
        child_name = child_data.get("name")
        child_buffer_type = child_data.get("buffer_type")
        child = self.children.get(child_name)

        # When dacite is casting a dict into a field of type Union,
        # it will go throught all the types and try to cast it until it works without exceptions
        # this is a way to sell dacite to go to the next type of the union
        if child_buffer_type is not expected_child_type.buffer_type:
            raise TypeError(
                f"Could not deserialize the buffer {child_name}: the expected child type is invalid"
            )

        # If the child already exists, we update it
        if child is not None:
            child.deserialize(child_data)
            return child

        # If the given child is a new child we construct it
        return expected_child_type.construct(child_data, self)

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        """
        Reconstruct this buffer from the given serialized data, this method is called
        recursively for all children that are modified.

        The data is applied as a patch, which means that you can pass partial data.
        However, when creating a children, you must give informations about
        the type of the children, when updating an existing one, it will keep the
        previous type:

        Example:
            Here are two ways to define the type of buffer for a new children
            here for a step buffer:

            foo:
                children:
                    bar:
                        name: "<name>"
                        buffer_type: "steps"

            foo:
                steps:
                    bar:
                        name: "<name>"
        """
        # Don't take the modifications of the hidden commands
        if self.hide and not force:
            return

        current_buffer_data = self.serialize()
        # The children's buffer_type can be given explicitly or passed by the key
        # (see docstring's example)
        serialized_data.setdefault("children", {})
        for child_type in self.get_child_types():
            children_data = serialized_data.get(child_type.buffer_type)
            if children_data is None:
                continue

            for child_data in children_data.values():
                child_data["buffer_type"] = child_type.buffer_type
            # Put all the children data into the children key
            serialized_data["children"].update(
                serialized_data.pop(child_type.buffer_type)
            )

        # If a children update some existing child, it inherit from its buffer type
        for child_name, child_data in serialized_data["children"].items():
            child_data["name"] = child_name
            current_children_data = current_buffer_data.get("children", {})
            existing_child_data = current_children_data.get(child_name)
            if existing_child_data is not None:
                child_data["buffer_type"] = existing_child_data["buffer_type"]

        # We don't want to re deserialize the existing children data
        current_buffer_data.pop("children", None)
        # Patch the current buffer's data
        serialized_data = jsondiff.patch(current_buffer_data, serialized_data)

        # Setup dacite to use our deserialize function has a type_hook to create the children
        config_data: Dict[str, Union[list, dict]] = {"cast": [Status, Connection]}
        if BaseBuffer not in self.get_child_types():
            config_data["type_hooks"] = {
                child_type: partial(self._deserialize_child, child_type)
                for child_type in self.get_child_types()
            }
        config = dacite_config.Config(**config_data)

        # Create a new buffer with the patched serialized data
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
        config = dacite_config.Config(cast=[Status, Connection])

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
