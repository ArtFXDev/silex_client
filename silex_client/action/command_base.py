from __future__ import annotations

import functools
from typing import List, TYPE_CHECKING, Any, Callable, Dict, Union

from silex_client.utils.enums import Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.command_buffer import CommandBuffer

# Type for parameters
CommandParameters = Dict[str, Dict[str, Union[Any]]]


class CommandBase:
    """
    Base class that every command should inherit from
    """

    #: Dictionary that represent the command's parameters
    parameters: CommandParameters = {}

    #: List that represent the required context metadata
    required_metadata: List[str] = []

    def __init__(self, command_buffer: CommandBuffer):
        self.command_buffer = command_buffer

    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ) -> Any:
        pass

    @property
    def type_name(self) -> str:
        """
        Shortcut to get the type name of the command
        """
        return self.__class__.__name__

    def check_parameters(self, parameters: CommandParameters) -> bool:
        """
        Check the if the input kwargs are valid accoring to the parameters list
        and conform it if nessesary
        """
        for parameter_name, parameter_value in parameters.items():
            if parameter_value is None:
                logger.error(
                    "Could not execute %s: The parameter %s is missing",
                    self.command_buffer.name,
                    parameter_name,
                )
                return False
        return True

    def check_context_metadata(self, context_metadata: Dict[str, Any]):
        """
        Check if the context snapshot stored in the buffer contains all the required
        data for the command
        """
        for metadata in self.required_metadata:
            if context_metadata.get(metadata) is None:
                logger.error(
                    "Could not execute command %s: The context is missing required metadata %s",
                    self.command_buffer.name,
                    metadata,
                )
                return False
        return True

    @staticmethod
    def conform_command():
        """
        Helper decorator that conform the input and the output
        Meant to be used with the __call__ method of CommandBase objects
        """

        def decorator_conform_command(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper_conform_command(
                command: CommandBase, *args, **kwargs
            ) -> None:
                # Make sure the given parameters are valid
                if not command.check_parameters(kwargs.get("parameters", args[1])):
                    command.command_buffer.status = Status.INVALID
                    return
                # Make sure all the required metatada is here
                if not command.check_context_metadata(
                    kwargs.get("action_query", args[2]).context_metadata
                ):
                    command.command_buffer.status = Status.INVALID
                    return
                # TODO: Find a way to catch all the errors and set the status to ERROR
                command.command_buffer.status = Status.PROCESSING
                await func(command, *args, **kwargs)
                if kwargs.get("action_query", args[2]).ws_connection.is_running:
                    await kwargs.get("action_query", args[2]).async_update_websocket()
                command.command_buffer.status = Status.COMPLETED

            return wrapper_conform_command

        return decorator_conform_command
