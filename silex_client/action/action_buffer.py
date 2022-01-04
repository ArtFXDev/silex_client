"""
@author: TD gang

Dataclass used to store the data related to an action
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.action.step_buffer import StepBuffer
from silex_client.utils.parameter_types import AnyParameter
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer


@dataclass()
class ActionBuffer(BaseBuffer):
    """
    Store the state of an action, it is used as a comunication payload with the UI
    """

    PRIVATE_FIELDS = [
        "store",
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]
    READONLY_FIELDS = ["label"]
    CHILD_NAME = "steps"

    #: Specify if the action must be simplified in the UI or not
    simplify: bool = field(compare=False, repr=False, default=False)
    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: The way this action is executed (backward, forward, paused...)
    execution_type: Execution = field(default=Execution.FORWARD)
    #: The status of the action, this value is readonly, it is computed from the commands's status
    thumbnail: Optional[str] = field(default=None)
    #: A dict of steps that will contain the commands
    children: Dict[str, StepBuffer] = field(default_factory=dict)
    #: Dict of variables that are global to all the commands of this action
    store: Dict[str, Any] = field(compare=False, default_factory=dict)
    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def child_type(self):
        return StepBuffer

    @property
    def steps(self) -> Dict[str, StepBuffer]:
        return self.children

    def deserialize(self, serialized_data: Dict[str, Any], force=False) -> None:
        super().deserialize(serialized_data, force)
        self.reorder_steps()

    def reorder_steps(self):
        """
        Place the steps in the right order accoring to the index value
        """
        self.children = dict(sorted(self.steps.items(), key=lambda item: item[1].index))

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
        and the datablass module tries to set it
        """

    @property
    def commands(self) -> List[CommandBuffer]:
        """
        Helper to get a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        return [
            command
            for step in self.steps.values()
            for command in step.commands.values()
        ]

    def get_parameter(
        self, step: str, command: str, name: str
    ) -> Optional[ParameterBuffer]:
        """
        Helper to get a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        command_buffer = self.steps[step].commands[command]
        return command_buffer.parameters.get(name, None)

    def set_parameter(
        self, step: str, command: str, name: str, value: Any, **kwargs
    ) -> None:
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
        if not isinstance(value, parameter.type) and parameter.type is not AnyParameter:
            try:
                value = parameter.type(value)
            except TypeError:
                logger.error(
                    "Could not set parameter %s: Invalid value (%s)", name, value
                )
                return

        parameter.value = value

        for key, value in kwargs.items():
            if not hasattr(parameter, key):
                logger.warning(
                    "Could not set the attribute %s on the parameter %s: The attribute does not exists",
                    key,
                    parameter,
                )
                continue
            setattr(parameter, key, value)
