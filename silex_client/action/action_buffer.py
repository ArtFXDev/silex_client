from __future__ import annotations

import uuid as unique_id
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, TYPE_CHECKING

import dacite

from silex_client.action.step_buffer import StepBuffer
from silex_client.utils.enums import Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.action.command_base import CommandParameters


@dataclass()
class ActionBuffer:
    """
    Store the state of an action, it is used as a comunication payload with the UI
    """

    # Define the mandatory keys and types for each attribibutes of a buffer
    STEP_TEMPLATE = {"index": int, "commands": list}
    COMMAND_TEMPLATE = {"path": str}

    #: The name of the action (usualy the same as the config file)
    name: str = field()
    #: A Unique ID to help differentiate multiple actions
    uuid: unique_id.UUID = field(default_factory=unique_id.uuid1)
    #: A dict of steps that will contain the commands
    steps: Dict[str, StepBuffer] = field(default_factory=dict)
    #: Dict of variables that are global to all the commands of this action
    variables: Dict[str, Any] = field(compare=False, default_factory=dict)
    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the action's data into json so it can be sent to the UI
        """
        return asdict(self)

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        new_data = dacite.from_dict(ActionBuffer, serialized_data)
        self.__dict__.update(new_data.__dict__)
        self.reorder_steps()

    def reorder_steps(self):
        self.steps = dict(sorted(self.steps.items(), key=lambda item: item[1].index))

    @property
    def status(self) -> Status:
        """
        The status of the action depends of the status of its commands
        """
        status = Status.COMPLETED
        for command in self.commands:
            status = command.status if command.status > status else status

        return status

    @property
    def commands(self, step: str = None) -> List[CommandBuffer]:
        """
        Helper to get a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        # Return the commands of the queried step
        if step is not None and step in self.steps.values():
            return list(self.steps[step].commands.values())

        # If no steps given return all the commands flattened
        return [
            command
            for step in self.steps.values()
            for command in step.commands.values()
        ]

    def get_parameter(self, step: str, command: str, name: str) -> CommandParameters:
        """
        Helper to get a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        command_buffer = self.steps[step].commands[command]
        return command_buffer.parameters.get(name, None)

    def set_parameter(self, step: str, command: str, name: str, value: Any) -> None:
        """
        Helper to set a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        parameter = self.get_parameter(step, command, name)
        if parameter is None:
            logger.error(
                "Could not set parameter %s: The parameter does not exists", name
            )
            return

        # Check if the given value is the right type
        if not isinstance(value, parameter.get("type", object)):
            try:
                value = parameter["type"](value)
            except TypeError:
                logger.error("Could not set parameter %s: Invalid value", name)
                return

        parameter["value"] = value
