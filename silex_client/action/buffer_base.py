"""
@author: TD gang

Dataclass used to store the data related to a command
"""

from __future__ import annotations

import copy
import re
import uuid as unique_id
import copy
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional, List

import dacite.config as dacite_config
import dacite.core as dacite
import jsondiff

from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.enums import Status


@dataclass()
class BaseBuffer:
    """
    Store the data of a buffer, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = [
        "output_result",
        "executor",
        "input_path",
        "outdated_cache",
        "serialize_cache",
    ]
    #: The list of fields that should be ignored when deserializing this buffer to json
    READONLY_FIELDS = ["logs", "label"]

    #: The name of the child
    CHILD_NAME = ""
    #: The name of the parent
    PARENT_NAME = ""

    #: Name of the buffer, must have no space or special characters
    name: str = field(default="unnamed")
    #: The name of the buffer, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: Parents in the buffer hierarchy of buffer of the action
    parent: Dict[str, BaseBuffer] = field(default_factory=dict)
    #: Childs in the buffer hierarchy of buffer of the action
    childs: Dict[str, BaseBuffer] = field(default_factory=dict)
    #: Specify if the buffer must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="No tooltip provided")
    #: A Unique ID to help differentiate multiple buffers
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))
    #: Marquer to know if the serialize cache is outdated or not
    outdated_cache: bool = field(compare=False, repr=False, default=True)
    #: Cache the serialize output
    serialize_cache: dict = field(compare=False, repr=False, default_factory=dict)

    def __setattr__(self, name, value):
        super().__setattr__("outdated_cache", True)
        super().__setattr__(name, value)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

    @property
    def child_type(self):
        return BaseBuffer

    @property
    def parent_type(self):
        return BaseBuffer

    @property
    def outdated_caches(self):
        """
        Check if the cache need to be recomputed by looking at the current cache
        and the childs caches
        """
        return self.outdated_cache or not all(
            not child.outdated_cache for child in self.childs.values()
        )

    def serialize(self, ignore_fields: List[str] = None) -> Dict[str, Any]:
        """
        Convert the buffer's data into json so it can be sent to the UI
        """
        if not self.outdated_caches:
            return self.serialize_cache

        if ignore_fields is None:
            ignore_fields = self.PRIVATE_FIELDS

        result = []

        for f in fields(self):
            if f.name in ignore_fields:
                continue
            elif f.name == "childs":
                childs = getattr(self, f.name)
                childs_value = {}
                for child_name, child in childs.items():
                    childs_value[child_name] = child.serialize()
                result.append((f.name, childs_value))
                continue

            result.append((f.name, getattr(self, f.name)))

        self.serialize_cache = copy.deepcopy(dict(result))
        self.outdated_cache = False
        return self.serialize_cache

    def _deserialize_childs(self, child_data: Any) -> Any:
        """
        Called bu deserialize to deserialize the childs of this buffer
        """
        child_name = child_data.get("name")
        child = self.childs.get(child_name)

        # If the given child is a new child we construct it
        if child is None:
            return self.child_type.construct(child_data)

        # Otherwise, we update the already existing one
        child.deserialize(child_data)
        return child

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        """
        Convert back the buffer's data from json into this object
        """
        # Don't take the modifications of the hidden commands
        if self.hide and not force:
            return

        # Patch the current buffer's data, except the chils data
        current_buffer_data = self.serialize()
        current_buffer_data = copy.copy(current_buffer_data)
        del current_buffer_data["childs"]
        serialized_data = jsondiff.patch(current_buffer_data, serialized_data)

        # Format the childs corectly, the name is defined in the key only
        for child_name, child in serialized_data.get(self.CHILD_NAME, {}).items():
            child["name"] = child_name

        # Create a new buffer with the patched serialized data
        config = dacite_config.Config(
            cast=[Status, CommandOutput],
            type_hooks={self.child_type: self._deserialize_childs},
        )
        new_buffer = dacite.from_dict(type(self), serialized_data, config)

        # Keep the current value for the private and readonly fields
        for private_field in self.PRIVATE_FIELDS + self.READONLY_FIELDS:
            setattr(new_buffer, private_field, getattr(self, private_field))

        # Update the current fields value with the new buffer's values
        self.childs.update(new_buffer.childs)
        new_buffer_data = new_buffer.__dict__
        del new_buffer_data.__dict__["childs"]
        self.__dict__.update(new_buffer_data)

        self.outdated_cache = True

    @classmethod
    def construct(cls, serialized_data: Dict[str, Any]) -> BaseBuffer:
        """
        Create an command buffer from serialized data

        The difference with deserialize and construct is that construct is used
        when the buffer is newly created, instead of updated
        """
        config = dacite_config.Config(cast=[Status, CommandOutput])

        # Initialize the buffer without the childs, since the childs needs special treatment
        filtered_data = serialized_data
        if cls.CHILD_NAME in serialized_data:
            filtered_data = copy.copy(serialized_data)
            del filtered_data[cls.CHILD_NAME]
        command = dacite.from_dict(cls, filtered_data, config)

        # Deserialize the newly created buffer to apply the childs
        command.deserialize(serialized_data, force=True)
        return command
