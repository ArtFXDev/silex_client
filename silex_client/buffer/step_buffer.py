from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from silex_client.buffer.base_buffer import BaseBuffer
from silex_client.buffer.command_buffer import CommandBuffer
from silex_client.utils.enums import Execution, Status


@dataclass()
class StepBuffer(BaseBuffer):
    """
    A step could be compared to a function that would contain
    multple statements (commands) or other functions (steps)

    Example:

        [StepBuffer]:
            [CommandBuffer]
            [CommandBuffer]
            [StepBuffer]:
                [CommandBuffer]
                [CommandBuffer]
    """

    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore

    #: The index defines the order in wich the steps are iterated
    index: int = field(default=0)

    #: This attribute follows the composite design pattern
    children: Dict[str, StepBuffer | CommandBuffer] = field(default_factory=dict)

    #: Dict of variables that are global to the children of this step (basically a tote)
    store: Dict[str, Any] = field(compare=False, default_factory=dict)

    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    #: The thumbnail is only for user display
    thumbnail: Optional[str] = field(default=None)

    #: Category when displaying the action in shelves of DCCs
    shelf: Optional[str] = field(default=None)

    def reorder_children(self):
        """
        Reorder children according to their index value
        """
        self.children = dict(
            sorted(self.children.items(), key=lambda item: item[1].index)
        )

    @property  # type: ignore
    def status(self) -> Status:
        """
        The status of the action depends of the status of its children
        """
        status = Status.COMPLETED
        for child in self.children.values():
            status = child.status if child.status > status else status

        # If some commands are completed and the rest initialized, then the action is processing
        children_statuses = [child.status for child in self.children.values()]
        if status is Status.INITIALIZED and Status.COMPLETED in children_statuses:
            status = Status.PROCESSING

        return status

    @status.setter
    def status(self, _) -> None:
        """
        The status property is readonly
        """
