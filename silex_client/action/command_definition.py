"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of CommandDefinition
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List
from silex_client.action.socket_buffer import SocketBuffer

from silex_client.utils.enums import Status

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.command_sockets import CommandSockets
    from silex_client.action.command_buffer import CommandBuffer


class CommandDefinition:
    """
    Base class that every command definition must inherit from

    To define the behaviour of your command you can override:
    - Methods:
        These three mehods must expect 3 arguments: parameters, action_query and logger.
        - __call__(): The code that will run when the command is executed
        - setup(): Hook that will run everytime a parameter is changed (before the execution)
        - undo(): Hook that will run when the user undo a command

    - Attribute:
        - inputs: Dict of SocketBuffers to define the expected input,
        the input values will be casted into the defined type
        - outputs: Dict of SocketBuffers to define the expected output,
        the returned value in the __call__ method must corresond to this declaration
        - required_metadata: List of data that a required to be in the context
        of execution of the command
    """

    #: Dictionary that represent the command's expected inputs
    inputs: Dict[str, Dict[str, Any]] = {}

    #: Dictionary that represent the command's expected outputs
    outputs: Dict[str, Dict[str, Any]] = {}

    #: List that represent the required context metadata
    required_metadata: List[str] = []

    def __init__(self, command_buffer: CommandBuffer):
        self.buffer = command_buffer

        self.inputs = {}
        self.outputs = {}

        # Merge the parameters of the inherited trees
        inheritance_tree = inspect.getmro(type(self))
        for inherited_class in inheritance_tree[::-1]:
            for socket in ["inputs", "outputs"]:
                if not hasattr(inherited_class, socket):
                    continue
                class_socket = getattr(inherited_class, socket)
                if isinstance(class_socket, dict):
                    getattr(self, socket).update(class_socket)

    @staticmethod
    def check_sockets(
        expected_sockets: Dict[str, dict],
        sockets: CommandSockets,
        logger: logging.Logger,
    ) -> bool:
        """
        Check the if the input/output values are all present and if their values
        can be casted
        """
        invalid_parameters: Dict[str, Exception] = {}
        for socket_name in expected_sockets:
            try:
                sockets[socket_name]
            except Exception as exception:
                invalid_parameters[socket_name] = exception

        if invalid_parameters:
            for key, value in invalid_parameters.items():
                logger.error("The socket %s is invalid: %s", key, value)
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
    def validate():
        """
        Helper decorator that makes sure all the parameter can be casted to the expected types,
        and the required metadata are present.
        By using this decorator, you make sure that invalid inputs/outputs will return
        a clear error before the execution of the command.
        """

        def decorator_validate(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper_validate(
                command: CommandDefinition,
                inputs: CommandSockets,
                action_query: ActionQuery,
                logger: logging.Logger,
            ) -> Any:
                # Make sure the given parameters are valid
                if not command.check_sockets(
                    command.inputs,
                    command.buffer.get_inputs_helper(action_query),
                    logger,
                ):
                    command.buffer.status = Status.INVALID
                    logger.error(
                        "Could not execute the command %s: Some parameters are invalid",
                        command.buffer.name,
                    )
                    return
                # Make sure all the required metatada is here
                if not command.check_context_metadata(
                    action_query.context_metadata, logger
                ):
                    command.buffer.status = Status.INVALID
                    logger.error(
                        "Could not execute the command %s: Some required metadata are missing",
                        command.buffer.name,
                    )
                    return

                await action_query.async_update_websocket()

                # Execution of the function
                output = await func(command, inputs, action_query, logger)

                if output is None:
                    return

                if not isinstance(output, dict):
                    command.buffer.status = Status.INVALID
                    logger.error(
                        "Error during the execution of the command %s: %s is not a dict",
                        command.buffer.name,
                        output,
                    )
                    return output

                for output_key, output_value in output.items():
                    if isinstance(command.buffer.outputs.get(output_key), SocketBuffer):
                        command.buffer.outputs[output_key].value = output_value

                # Make sure the returned output is valid
                if not command.check_sockets(
                    command.outputs,
                    command.buffer.get_outputs_helper(action_query),
                    logger,
                ):
                    command.buffer.status = Status.INVALID
                    logger.error(
                        "Error during the execution of the command %s: Invalid retured values %s",
                        command.buffer.name,
                        output,
                    )
                    return output

                await action_query.async_update_websocket()
                return output

            return wrapper_validate

        return decorator_validate

    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        """
        Override this method to implement the behaviour of your command
        """

    async def undo(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        """
        Override this method as a hook executed when the user undo this command
        """

    async def setup(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        """
        Override this method as a hook executed when a parameter is changed and before
        the command is executed
        """
