"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of ActionBuffer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Union

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.action.step_buffer import StepBuffer
from silex_client.utils.enums import Status

TBaseBuffer = TypeVar("TBaseBuffer", bound="BaseBuffer")


@dataclass()
class ActionBuffer(BaseBuffer):
    """
    Store the data of an action, an action can have a step or an other actions as children.
    It could be compared to a function, it can be inserted in other actions, and store a series
    of commands to execute, grouped into steps.
    """

    PRIVATE_FIELDS = [
        "store",
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="actions")
    #: Specify if the action must be simplified in the UI or not
    simplify: bool = field(compare=False, repr=False, default=False)
    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: The status of the action, this value is readonly, it is computed from the commands's status
    thumbnail: Optional[str] = field(default=None)
    #: An action can have other actions or steps as children
    children: Dict[str, Union[StepBuffer, ActionBuffer]] = field(default_factory=dict)
    #: Dict of variables that are global to all the commands of this action
    store: Dict[str, Any] = field(compare=False, default_factory=dict)
    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        super().deserialize(serialized_data, True)

    @property  # type: ignore
    def status(self) -> Status:
        """
        The status of the action depends of the status of its commands
        """
        status = Status.COMPLETED
        for command in self.commands:
            status = command.status if command.status > status else status

        # If some commands are completed and the rest initialized, then the action is processing
        if status is Status.INITIALIZED and Status.COMPLETED in [
            command.status for command in self.commands
        ]:
            status = Status.PROCESSING

        return status

    @status.setter
    def status(self, _) -> None:
        """
        The status property is readonly, however
        we need to implement this since it is also a property
        and the dataclass module tries to set it
        """

    @property
    def commands(self) -> List[CommandBuffer]:
        """
        Helper to get the commands of the actions
        """

        def flatten(nested_list: List[Union[StepBuffer, ActionBuffer, CommandBuffer]]):
            for item in sorted(nested_list, key=lambda x: x.index):
                if isinstance(item, CommandBuffer):
                    yield item
                else:
                    yield from flatten(list(item.children.values()))

        return list(flatten(list(self.children.values())))

    def get_command(self, command_path: List[str]) -> Optional[CommandBuffer]:
        """
        Helper to get a parameter of a command that belong to this action
        """
        return self.get_child(command_path, CommandBuffer)
