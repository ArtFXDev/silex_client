from abc import ABC, abstractmethod
from typing import Union, Callable
import functools

from silex_client.action.command_buffer import CommandBuffer
from silex_client.utils.log import logger


class CommandBase(ABC):
    """
    Base class that every command should inherit from
    """

    # List if dictionaries that represent the command's parameters
    parameters = []

    def __init__(self, command_buffer: CommandBuffer):
        self.command_buffer = command_buffer

    @abstractmethod
    def __call__(self, **kwargs):
        pass

    @property
    def type_name(self):
        # Shortcut to get the type name of the command
        return self.__class__.__name__

    def check_kwargs(self, kwargs: dict) -> Union[dict, None]:
        """
        Check the if the input kwargs are valid accoring to the parameters list
        and conform it if nessesary
        """
        for parameter in self.parameters:
            if parameter["name"] not in kwargs.keys():
                # Find default value or return error
                if "default" in parameter and parameter["default"] is not None:
                    kwargs[parameter["name"]] = parameter["default"]
                else:
                    logger.error("Missing parameter for command %s" %
                                 type(self))
                    return None

        # Return the conformised kwargs
        return kwargs

    def update_buffer(self, return_code: int = 0):
        self.command_buffer.return_code = return_code
        # TODO: Send feedback to the UI

    @staticmethod
    def conform_command(func: Callable) -> Callable:
        """
        Helper decorator that conform the input and the output
        """
        @functools.wraps(func)
        def wrapper_conform_command(*args, **kwargs) -> None:
            # Make sure the given arguments are valid parameters
            kwargs = args[0].check_kwargs(kwargs)
            if kwargs is None:
                return
            # Call the initial function
            func(*args, **kwargs)
            # Update buffer for feedback
            args[0].update_buffer()

        return wrapper_conform_command
