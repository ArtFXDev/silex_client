"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of StepBuffer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.enums import Status


@dataclass()
class StepBuffer(BaseBuffer):
    """
    Store the data of a step. A step is only for grouping commands into categories, it helps
    for readability, and allows to hide/skip... multiple commands at once
    """

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="steps")
    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: A step can only have commands as children
    children: Dict[str, CommandBuffer] = field(default_factory=dict)

    @property
    def commands(self) -> List[CommandBuffer]:
        """
        Alias for children as a list
        """
        return list(self.children.values())

    @property  # type: ignore
    def status(self) -> Status:
        """
        The status of the action depends of the status of its commands
        """
        status = Status.COMPLETED
        for command in self.commands:
            status = command.status if command.status > status else status

        # If some commands are completed and the rest initialized, then the step is processing
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
        and the datablass module tries to set it
        """
