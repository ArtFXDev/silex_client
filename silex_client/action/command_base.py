from __future__ import annotations
from typing import Callable
import functools
import typing

from silex_client.utils.log import logger
from silex_client.utils.enums import Status

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.command_buffer import CommandBuffer
    from silex_client.action.action_query import ActionQuery


class CommandBase():
    """
    Base class that every command should inherit from
    """

    #: Dictionary that represent the command's parameters
    parameters: dict = {}

    #: List that represent the required context metadata
    required_metada: list = []

    def __init__(self, command_buffer: CommandBuffer):
        self.command_buffer = command_buffer

    async def __call__(self, parameters: dict, action_query: ActionQuery):
        pass

    @property
    def type_name(self):
        """
        Shortcut to get the type name of the command
        """
        return self.__class__.__name__

    def check_parameters(self, parameters: dict) -> bool:
        """
        Check the if the input kwargs are valid accoring to the parameters list
        and conform it if nessesary
        """
        for parameter_name, parameter_value in parameters.items():
            if parameter_value is None:
                logger.error(
                    "Could not execute %s: The parameter %s is missing",
                    self.command_buffer.name, parameter_name)
                return False
        return True

    def check_context_metadata(self, context_metadata):
        """
        Check if the context snapshot stored in the buffer contains all the required
        data for the command
        """
        for metadata in self.required_metada:
            if context_metadata.get(metadata) is None:
                logger.error(
                    "Could not execute command %s: The context is missing required metadata %s",
                    self.command_buffer.name, metadata)
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
            async def wrapper_conform_command(command: CommandBase, *args,
                                        **kwargs) -> None:
                # Make sure the given parameters are valid
                if not command.check_parameters(
                        kwargs.get("parameters", args[0])):
                    command.command_buffer.status = Status.INVALID
                    return
                # Make sure all the required metatada is here
                if not command.check_context_metadata(
                        kwargs.get("action_query", args[1]).context_metadata):
                    command.command_buffer.status = Status.INVALID
                    return
                # Call the initial function while catching all the errors
                # because we want to update the status
                try:
                    command.command_buffer.status = Status.PROCESSING
                    await func(command, *args, **kwargs)
                    command.command_buffer.status = Status.COMPLETED
                except Exception as exception:
                    command.command_buffer.status = Status.ERROR
                    raise exception

            return wrapper_conform_command

        return decorator_conform_command
