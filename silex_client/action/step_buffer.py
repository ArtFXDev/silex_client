"""
@author: TD gang

Dataclass used to store the data related to a step
"""

import re
import uuid as unique_id
from dataclasses import asdict, dataclass, field
from typing import Dict, Union, Any

import dacite

from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.enums import Status


@dataclass()
class StepBuffer:
    """
    Store the data of a step, it is used as a comunication payload with the UI
    """

    #: Name of the step, must have no space or special characters
    name: str
    #: The index of the step, to set the order in which they should be executed
    index: int
    #: The status of the step, this value is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: The name of the step, meant to be displayed
    label: Union[str, None] = field(compare=False, repr=False, default=None)
    #: Specify if the step must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="")
    #: Dict that represent the parameters of the command, their type, value, name...
    commands: Dict[str, CommandBuffer] = field(default_factory=dict)
    #: A Unique ID to help differentiate multiple actions
    uuid: Union[unique_id.UUID, str] = field(default_factory=unique_id.uuid1)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        return asdict(self)

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        new_data = dacite.from_dict(StepBuffer, serialized_data)
        self.__dict__ = new_data.__dict__

    @property  # type: ignore
    def status(self) -> Status:
        """
        The status of the action depends of the status of its commands
        """
        status = Status.COMPLETED
        for command in self.commands.values():
            status = command.status if command.status > status else status

        return status

    @status.setter
    def status(self, other) -> None:
        """
        The status property is readonly, however
        we need to implement this since it is also a property
        and the datablass module tries to set it
        """
