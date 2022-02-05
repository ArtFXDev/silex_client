"""
@author: TD gang
@github: https://github.com/ArtFXDev

Class definition of CommandBuffer
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, TypeVar, Union, Tuple

import jsondiff

from silex_client.action.base_buffer import BaseBuffer
from silex_client.action.abstract_socket import AbstractSocketBuffer
from silex_client.action.command_definition import CommandDefinition
from silex_client.network.websocket_log import RedirectWebsocketLogs
from silex_client.utils.enums import Execution, Status
from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery

GenericType = TypeVar("GenericType")


@dataclass()
class CommandBuffer(BaseBuffer):
    """
    Store the data of a command. A command can be executed, it stores a path to a CommandDefinition
    that will contain the code to execute. The CommandBuffer is responsible to gather the input data
    for the execution of the command.
    """

    PRIVATE_FIELDS = [
        "defintion",
        "parent",
        "outdated_cache",
        "serialize_cache",
    ]

    READONLY_FIELDS = ["status", "buffer_type", "logs"]

    #: Type name to help differentiate the different buffer types
    buffer_type: str = field(default="commands")
    #: The path to the command's definition is a regular python import, with '.' as a separator
    definition_path: str = field(default="")
    #: Specify if the command should be asking to the UI a user input
    prompt: bool = field(compare=False, repr=False, default=False)
    #: The status of the command, to keep track of the progression, specify the errors
    status: Status = field(default=Status.INITIALIZED, init=False)
    #: The definition of the code to execute when the command is executed
    definition: CommandDefinition = field(init=False)
    #: List of all the logs during the execution of that command
    logs: List[Dict[str, str]] = field(default_factory=list)

    def _get_definition(self) -> CommandDefinition:
        """
        Try to import the module, get and instantiate the CommandDefinition object
        """
        try:
            # We cannot import the class directly, we must split the module from the class,
            # import the module and get the class from the module afterwards
            (*module_path, class_name) = self.definition_path.split(".")

            # Import the module
            module = importlib.import_module(".".join(module_path))
            importlib.reload(module)

            # Get the command class
            definition = getattr(module, class_name)

            if not issubclass(definition, CommandDefinition):
                raise ImportError("The given command does not inherit from CommandBase")

            return definition(self)

        except (ImportError, AttributeError, ModuleNotFoundError) as exception:
            raise Exception(f"Invalid command path: {self.definition_path}") from exception

    async def execute(
        self, action_query: ActionQuery, execution_type: Execution = Execution.FORWARD
    ):
        """
        Execute the command using the executor
        """
        if self.skip_execution():
            logger.debug("Skipping command %s", self.name)
        else:
            parameters = CommandInputsHelper(action_query, self)
            logger.debug("Executing command %s", self.name)
            async with RedirectWebsocketLogs(action_query, self) as log:
                # Set the status to processing
                self.status = Status.PROCESSING

                # Call the actual command
                if execution_type == Execution.FORWARD:
                    await self.definition(parameters, action_query, log)
                elif execution_type == Execution.BACKWARD:
                    await self.definition.undo(parameters, action_query, log)

        # Keep the error statuses
        if self.status in [Status.INVALID, Status.ERROR]:
            return
        # Set the status to completed or initialized according to the execution
        if execution_type == Execution.FORWARD:
            self.status = Status.COMPLETED
        elif execution_type == Execution.BACKWARD:
            self.status = Status.INITIALIZED

    def require_prompt(self, action_query: ActionQuery) -> bool:
        """
        Check if this command require a user input, by testing the prompt field
        and none values on the input
        """
        if self.skip:
            return False
        if self.prompt:
            return True
        if all(
            input_buffer.eval(action_query) is not None or input_buffer.hide
            for input_buffer in self.inputs.values()
        ):
            return False
        return True

    async def setup(self, action_query: ActionQuery):
        """
        Call the setup of the command, the setup method is used to edit the command attributes
        dynamically (parameters, states...)
        """
        parameters = CommandInputsHelper(action_query, self)
        async with RedirectWebsocketLogs(action_query, self) as log:
            await self.definition.setup(parameters, action_query, log)

    @classmethod
    def construct(
        cls, serialized_data: Dict[str, Any], parent: BaseBuffer = None
    ) -> CommandBuffer:
        """
        The construct of a command is different from others since the command
        first inerit it's data from the command definition and then is overriden
        by the input data
        """
        if "definition_path" not in serialized_data:
            raise Exception("Could not create command buffer: The definition path is required")

        buffer = cls(definition_path=serialized_data["definition_path"], parent=parent)
        command_definition = buffer._get_definition()

        for socket in ["inputs", "outputs"]:
            socket_definition = getattr(command_definition, socket)
            socket_serialized = serialized_data[socket]

            for socket_name, socket_data in socket_definition.items():
                socket_data["name"] = socket_name

                # The socket can be defined with <key>=<value> directly as a shortcut
                if not isinstance(socket_serialized.get(socket_name, {}), dict):
                    socket_serialized[socket_name] = {"input": socket_serialized[socket_name]}

                # Apply the serialied socket to override the default values in the socket definition
                socket_definition[socket_name] = jsondiff.patch(
                    socket_definition[socket_name], socket_serialized.get(socket_name, {})
                )

            serialized_data[socket] = socket_definition

        return super().construct(serialized_data, parent)

class CommandSocketsHelper:
    """
    Helper to get and set the input/output values of a command quickly.
    Act like a dictionary
    """

    def __init__(
        self,
        action_query: ActionQuery,
        command: CommandBuffer,
        data: Dict[str, AbstractSocketBuffer],
    ):
        self.action_query = action_query
        self.command = command
        self.data = data

    def __getitem__(self, key: str):
        return self.data[key].eval(self.action_query)

    def __setitem__(self, key: str, value: Any):
        self.data[key].input = value

    def get(self, key: str, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value.
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default
        return self.__getitem__(key)

    def get_raw(self, key, default: GenericType = None) -> Union[Any, GenericType]:
        """
        Return the parameter's value without casting it to the expected type
        Return the default if the parametr does not exists
        """
        if key not in self.data:
            return default
        return self.data[key].input

    def get_buffer(self, key) -> AbstractSocketBuffer:
        """
        Return the parameter buffer directly
        """
        return self.data[key]

    def keys(self) -> List[str]:
        """Same method a the original dict"""
        return list(self.data.keys())

    def values(self) -> List[Any]:
        """Same method a the original dict"""
        return [child.eval(self.action_query) for child in self.data.values()]

    def items(self) -> List[Tuple[str, Any]]:
        """Same method a the original dict"""
        return [
            (key, value.eval(self.action_query))
            for key, value in self.data.items()
        ]

    def update(self, values: Union[CommandSocketsHelper, Dict[str, Any]]):
        """Update the values with the given dict"""
        for key, value in values.items():
            self[key] = value


class CommandInputsHelper(CommandSocketsHelper):
    """
    Helper to get and set the input values of a command quickly.
    Act like a dictionary
    """
    def __init__(self, action_query: ActionQuery, command: CommandBuffer):
        super().__init__(action_query, command, command.inputs)


class CommandOutputsHelper(CommandSocketsHelper):
    """
    Helper to get and set the output values of a command quickly.
    Act like a dictionary
    """
    def __init__(self, action_query: ActionQuery, command: CommandBuffer):
        super().__init__(action_query, command, command.outputs)
