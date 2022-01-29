"""
@author: TD gang

Base class that every command should inherit from
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from silex_client.utils.enums import Status

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.command_buffer import CommandBuffer, CommandParameters
    from silex_client.action.parameter_buffer import ParameterBuffer


class CommandBase:
    """
    Base class that every command should inherit from
    """

    #: Dictionary that represent the command's parameters
    parameters: Dict[str, Dict[str, Any]] = {}

    #: List that represent the required context metadata
    required_metadata: List[str] = []

    def __init__(self, command_buffer: CommandBuffer):
        self.command_buffer = command_buffer
        self.history_require_prompt = command_buffer.require_prompt()
        inheritance_tree = inspect.getmro(type(self))

        # Merge the parameters of the inherited trees
        self.parameters = {}
        for inherited_class in inheritance_tree[::-1]:
            if not hasattr(inherited_class, "parameters"):
                continue
            class_parameters = getattr(inherited_class, "parameters")
            if isinstance(class_parameters, dict):
                self.parameters.update(class_parameters)

    def check_parameters(
        self, parameters: CommandParameters, logger: logging.Logger
    ) -> bool:
        """
        Check the if the parameter values are all present and if their values
        can be casted
        """
        invalid_parameters: Dict[str, Exception] = {}
        for parameter_name in self.parameters:
            try:
                parameters[parameter_name]
            except Exception as exception:
                invalid_parameters[parameter_name] = exception

        if invalid_parameters:
            for key, value in invalid_parameters.items():
                logger.error("The parameter %s is invalid: %s", key, value)

            return False
        return True

    def check_context_metadata(
        self, context_metadata: Dict[str, Any], logger: logging.Logger
    ):
        """
        Check if the context snapshot stored in the buffer contains all the required
        data for the command
        """
        return_value = True
        for metadata in self.required_metadata:
            if metadata not in context_metadata:
                logger.error("The context is missing required metadata %s", metadata)
                return_value = False
        return return_value

    @staticmethod
    def conform_command():
        """
        Helper decorator that makes sure all the parameter can be casted to the expected types,
        and the required metadata are present
        Meant to be used with the __call__ method of CommandBase objects
        """

        def decorator_conform_command(
            func: Callable[
                [CommandBase, CommandParameters, ActionQuery, logging.Logger], Any
            ]
        ) -> Callable:
            @functools.wraps(func)
            async def wrapper_conform_command(
                command: CommandBase,
                parameters: CommandParameters,
                action_query: ActionQuery,
                logger: logging.Logger,
            ) -> None:
                # Make sure the given parameters are valid
                if not command.check_parameters(parameters, logger):
                    command.command_buffer.status = Status.INVALID
                    logger.error(
                        "Could not execute the command %s: Some parameters are invalid",
                        command.command_buffer.name,
                    )
                    return
                # Make sure all the required metatada is here
                if not command.check_context_metadata(
                    action_query.context_metadata, logger
                ):
                    command.command_buffer.status = Status.INVALID
                    logger.error(
                        "Could not execute the command %s: Some required metadata are missing",
                        command.command_buffer.name,
                    )
                    return

                await action_query.async_update_websocket()

                output = await func(command, parameters, action_query, logger)
                command.command_buffer.data_out = output

                await action_query.async_update_websocket()
                return output

            return wrapper_conform_command

        return decorator_conform_command

    async def prompt_user(
        self, action_query: ActionQuery, new_parameters: dict[str, ParameterBuffer]
    ) -> CommandParameters:
        """
        Add the given parameters to to current command parameters and ask an update from the user
        """
        command_parameters = CommandParameters(action_query, self.command_buffer)
        if not action_query.ws_connection.is_running:
            return command_parameters

        # Hide the existing parameters
        for parameter in self.command_buffer.parameters.values():
            parameter.hide = True
        # Add the parameters to the command buffer's parameters
        self.command_buffer.parameters.update(new_parameters)
        self.command_buffer.ask_user = True

        await action_query.prompt_commands(end=action_query.current_command_index + 1)
        return command_parameters

    async def __call__(
        self,
        parameters: CommandParameters,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        raise NotImplementedError("This command does not have any execution function")

    async def undo(
        self,
        parameters: CommandParameters,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        self.command_buffer.ask_user = self.history_require_prompt

    async def setup(
        self,
        parameters: CommandParameters,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        pass
