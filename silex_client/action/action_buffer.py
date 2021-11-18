"""
@author: TD gang

Dataclass used to store the data related to an action
"""

from __future__ import annotations

import uuid as unique_id
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import re

import dacite.config as dacite_config
import dacite.core as dacite

from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.action.step_buffer import StepBuffer
from silex_client.utils.datatypes import CommandOutput
from silex_client.utils.parameter_types import AnyParameter
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer


@dataclass()
class ActionBuffer:
    """
    Store the state of an action, it is used as a comunication payload with the UI
    """

    # Define the mandatory keys and types for each attribibutes of a buffer
    STEP_TEMPLATE = {"index": int, "commands": list}
    COMMAND_TEMPLATE = {"path": str}
    #: The list of fields that should be ignored when serializing this buffer to json
    PRIVATE_FIELDS = ["variables"]

    #: The name of the action (usualy the same as the config file)
    name: str = field()
    #: A Unique ID to help differentiate multiple actions
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))
    #: The name of the command, meant to be displayed
    label: Optional[str] = field(compare=False, repr=False, default=None)
    #: Specify if the action must be displayed by the UI or not
    hide: bool = field(compare=False, repr=False, default=False)
    #: Specify if the action must be displayed by the shelf or not
    shelf: bool = field(compare=False, repr=False, default=True)
    #: The status of the action, this value is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: The way this action is executed (backward, forward, paused...)
    execution_type: Execution = field(default=Execution.FORWARD)
    #: The status of the action, this value is readonly, it is computed from the commands's status
    thumbnail: Optional[str] = field(default=None)
    #: A dict of steps that will contain the commands
    steps: Dict[str, StepBuffer] = field(default_factory=dict)
    #: Dict of variables that are global to all the commands of this action
    variables: Dict[str, Any] = field(compare=False, default_factory=dict)
    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command label
        if self.label is None:
            self.label = slugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

    def serialize(self) -> Dict[str, Any]:
        """
        Convert the action's data into json so it can be sent to the UI
        """
        result = []

        for f in fields(self):
            if f.name == "steps":
                steps = getattr(self, f.name)
                step_value = {}
                for step_name, step in steps.items():
                    step_value[step_name] = step.serialize()
                result.append((f.name, step_value))
            elif f.name in self.PRIVATE_FIELDS:
                continue
            else:
                result.append((f.name, getattr(self, f.name)))

        return dict(result)

    def _deserialize_steps(self, step_data: Any) -> Any:
        step_name = step_data.get("name")
        step = self.steps.get(step_name)
        if step is None:
            return StepBuffer.construct(step_data)

        step.deserialize(step_data)
        return step

    def deserialize(self, serialized_data: Dict[str, Any]) -> None:
        """
        Convert back the action's data from json into this object
        """
        # Format the steps corectly
        for step_name, step in serialized_data.get("steps", {}).items():
            step["name"] = step_name

        config = dacite_config.Config(
            cast=[Status, Execution, CommandOutput],
            type_hooks={StepBuffer: self._deserialize_steps},
        )
        new_data = dacite.from_dict(ActionBuffer, serialized_data, config)

        for private_field in self.PRIVATE_FIELDS:
            setattr(new_data, private_field, getattr(self, private_field))

        self.__dict__.update(new_data.__dict__)
        self.reorder_steps()

    def reorder_steps(self):
        """
        Place the steps in the right order accoring to the index value
        """
        self.steps = dict(
            sorted(self.steps.items(), key=lambda item: item[1].index))

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
    def status(self, other) -> None:
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
                logger.error("Could not set parameter %s: Invalid value (%s)", name, value)
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
