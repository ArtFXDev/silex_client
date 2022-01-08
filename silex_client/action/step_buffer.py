"""
@author: TD gang

Dataclass used to store the data related to a step
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.enums import Status


@dataclass()
class StepBuffer(BaseBuffer):
    """
    Store the data of a step, it is used as a comunication payload with the UI
    """

    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = ["outdated_cache", "serialize_cache", "parent"]
    READONLY_FIELDS = ["label"]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="steps")
    #: The index of the step, to set the order in which they should be executed
    index: int = field(default=0)
    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: Dict that represent the parameters of the command, their type, value, name...
    children: Dict[str, CommandBuffer] = field(default_factory=dict)

    @staticmethod
    def get_child_type():
        return CommandBuffer

    @property
    def commands(self) -> Dict[str, CommandBuffer]:
        return self.children

    @property  # type: ignore
    def status(self) -> Status:
        """
        The status of the action depends of the status of its commands
        """
        status = Status.COMPLETED
        for command in self.commands.values():
            status = command.status if command.status > status else status

        # If some commands are completed and the rest initialized, then the step is processing
        if status is Status.INITIALIZED and Status.COMPLETED in [
            command.status for command in self.commands.values()
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
