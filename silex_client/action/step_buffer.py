from dataclasses import dataclass, field, asdict
from typing import Union
import re

@dataclass()
class StepBuffer():
    """
    Store the data of a step, it is used as a comunication payload with the UI
    """

    #: Name of the step, must have no space or special characters
    name: str
    #: The index of the step, to set the order in which they should be executed
    index: int
    #: The name of the step, meant to be displayed
    label: Union[str, None] = field(compare=False, repr=False, default=None)
    #: Specify if the step must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Small explanation for the UI
    tooltip: str = field(compare=False, repr=False, default="")
    #: Dict that represent the parameters of the command, their type, value, name...
    commands: dict = field(compare=False, repr=False, default_factory=dict)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

    def serialize(self) -> dict:
        """
        Convert the command's data into json so it can be sent to the UI
        """
        return asdict(self)

    @classmethod
    def deserialize(cls, serealised_data: dict):
        """
        Convert back the action's data from json into this object
        """
        raise NotImplementedError("This feature is WIP")
