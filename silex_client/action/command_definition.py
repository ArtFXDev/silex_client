"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of CommandDefinition
"""

from __future__ import annotations

import functools
import inspect
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Union
from silex_client.action.socket_buffer import SocketBuffer

from silex_client.utils.enums import Status

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery
    from silex_client.action.command_buffer import CommandBuffer, CommandSocketsHelper


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
        expected_sockets: Dict[str, dict], sockets: CommandSocketsHelper, logger: logging.Logger
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
    def conform_command():
        """
        Helper decorator that makes sure all the parameter can be casted to the expected types,
        and the required metadata are present.
        By using this decorator, you make sure that invalid inputs/outputs will return 
        a clear error before the execution of the command.
        """

        def decorator_conform_command(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper_conform_command(
                command: CommandDefinition,
                inputs: CommandSocketsHelper,
                action_query: ActionQuery,
                logger: logging.Logger,
            ) -> Any:
                # Make sure the given parameters are valid
                if not command.check_sockets(command.inputs, command.buffer.get_inputs_helper(action_query), logger):
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

                output = await func(command, inputs, action_query, logger)
                command.buffer.output = output

                # Make sure the returned output is valid
                if not command.check_sockets(command.outputs, command.buffer.get_outputs_helper(action_query), logger):
                    command.buffer.status = Status.INVALID
                    logger.error(
                        "Error during the execution of the command %s: Invalid retured values %s",
                        command.buffer.name,
                        command.buffer.outputs,
                    )
                    return

                await action_query.async_update_websocket()
                return output

            return wrapper_conform_command

        return decorator_conform_command

    async def prompt_user(
        self,
        action_query: ActionQuery,
        new_inputs: dict[str, Union[SocketBuffer, dict]],
    ) -> CommandSocketsHelper:
        """
        Add the given parameters to to current command parameters and ask an update from the user
        """
        command_parameters = self.buffer.get_inputs_helper(action_query)
        if not action_query.ws_connection.is_running:
            return command_parameters

        # Hide the existing parameters
        for input_buffer in self.buffer.inputs.values():
            input_buffer.hide = True

        # Cast the parameters that are dict into SocketBuffer
        socket_buffers: Dict[str, SocketBuffer] = {}
        for socket_name, socket in new_inputs.items():
            if isinstance(socket, SocketBuffer):
                socket_buffers[socket_name] = socket
                continue
            socket_buffers[socket_name] = SocketBuffer.construct(socket, self.buffer)

        # Add the parameters to the command buffer's parameters
        self.buffer.inputs.update(socket_buffers)
        self.buffer.prompt = True

        await action_query.prompt_commands(end=action_query.current_command_index + 1)
        return command_parameters

    async def __call__(
        self,
        parameters: CommandSocketsHelper,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        raise NotImplementedError("This command does not have any execution function")

    async def undo(
        self,
        parameters: CommandSocketsHelper,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        pass

    async def setup(
        self,
        parameters: CommandSocketsHelper,
        action_query: ActionQuery,
        logger: logging.Logger,
    ) -> Any:
        pass
