"""
@author: TD gang

Dataclass used to store the data related to an action
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TypeVar, Type

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.command_buffer import CommandBuffer
from silex_client.action.parameter_buffer import ParameterBuffer
from silex_client.action.step_buffer import StepBuffer
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger
from silex_client.utils.parameter_types import AnyParameter

TBaseBuffer = TypeVar("TBaseBuffer", bound="BaseBuffer")


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

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="actions")
    #: Specify if the action must be simplified in the UI or not
    simplify: bool = field(compare=False, repr=False, default=False)
    #: The status is readonly, it is computed from the commands's status
    status: Status = field(init=False)  # type: ignore
    #: The way this action is executed (backward, forward, paused...)
    execution_type: Execution = field(default=Execution.FORWARD)
    #: The status of the action, this value is readonly, it is computed from the commands's status
    thumbnail: Optional[str] = field(default=None)
    #: A dict of steps that will contain the commands
    children: Dict[str, Union[StepBuffer, ActionBuffer]] = field(default_factory=dict)
    #: The index of the action, this field is only used for subactions
    index: int = field(default=0)
    #: Dict of variables that are global to all the commands of this action
    store: Dict[str, Any] = field(compare=False, default_factory=dict)
    #: Snapshot of the context's metadata when this buffer is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def steps(self) -> Dict[str, Union[StepBuffer, ActionBuffer]]:
        """
        Alias for children
        """
        return self.children

    def deserialize(self, serialized_data: Dict[str, Any], _=False) -> None:
        super().deserialize(serialized_data, True)
        self.reorder_steps()

    def reorder_steps(self):
        """
        Place the steps in the right order accoring to the index value
        """
        self.children = dict(
            sorted(self.children.items(), key=lambda item: item[1].index)
        )

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
        Helper to get the commands of the actions
        The data is quite nested, this is just for conveniance
        """

        def flatten(nested_list: List[Union[StepBuffer, ActionBuffer, CommandBuffer]]):
            for item in nested_list:
                if isinstance(item, CommandBuffer):
                    yield item
                else:
                    yield from flatten(list(item.children.values()))

        return list(flatten(list(self.children.values())))

    def get_child(
        self, child_path: List[str], child_type: Type[TBaseBuffer]
    ) -> Optional[TBaseBuffer]:
        """
        Helper to get a child that belong to this action from a path
        The data is quite nested, this is just for conveniance
        """
        if not child_path:
            logger.error("Could not get the child %s: Invalid path", child_path)
            return None

        child = self
        for key in child_path:
            if not isinstance(child, BaseBuffer):
                logger.error(
                    "Could not get the child %s: Invalid path",
                    child_path,
                )
                return None
            child = child.children.get(key)

        if not isinstance(child, child_type):
            logger.error(
                "Could not get the child %s: %s is not of type %s",
                child_path,
                child,
                child_type,
            )
            return None

        return child

    def get_command(self, command_path: List[str]) -> Optional[CommandBuffer]:
        """
        Helper to get a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        return self.get_child(command_path, CommandBuffer)

    def get_parameter(self, parameter_path: List[str]) -> Optional[ParameterBuffer]:
        """
        Helper to get a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        return self.get_child(parameter_path, ParameterBuffer)

    def set_parameter(self, parameter_path: List[str], value: Any, **kwargs) -> None:
        """
        Helper to set a parameter of a command that belong to this action
        The data is quite nested, this is just for conveniance
        """
        parameter = self.get_parameter(parameter_path)
        if parameter is None:
            logger.error(
                "Could not set parameter %s: The parameter does not exists",
                parameter_path,
            )
            return

        # Check if the given value is the right type
        if not isinstance(value, parameter.type) and parameter.type is not AnyParameter:
            try:
                value = parameter.type(value)
            except TypeError:
                logger.error(
                    "Could not set parameter %s: Invalid value (%s)",
                    parameter_path,
                    value,
                )
                return

        parameter.value = value

        for attribute_name, attribute_value in kwargs.items():
            if not hasattr(parameter, attribute_name):
                logger.warning(
                    "Could not set the attribute %s on the parameter %s: The attribute does not exists",
                    attribute_name,
                    parameter,
                )
                continue
            setattr(parameter, attribute_name, attribute_value)
