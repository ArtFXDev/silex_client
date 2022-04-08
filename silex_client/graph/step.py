from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from silex_client.graph.graph_item import GraphItem
from silex_client.graph.pluggable_item import PluggableItem
from silex_client.graph.command import Command
from silex_client.utils.enums import Status


@dataclass()
class Step(GraphItem, PluggableItem):
    """
    A step could be compared to a function that would contain
    multple statements (commands) or other functions (steps)

    Example:

    [Action]
        [Step]:
            [Command]
            [Command]
            [Step]:
                [Command]
                [Command]
    """

    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore

    #: The index defines the order in wich the steps are iterated
    index: int = field(default=0)

    #: This attribute follows the composite design pattern
    children: Dict[str, Step | Command] = field(default_factory=dict)

    #: Dict of variables that are global to the children of this step (basically a tote)
    store: Dict[Any, Any] = field(compare=False, default_factory=dict)

    #: Overrides of the action's context metadata for this step
    context_overrides: Dict[str, Any] = field(default_factory=dict)

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
