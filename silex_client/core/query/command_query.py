"""
@author: TD gang

Entry point for every action. This class is here to execute, and edit actions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from silex_client.utils.log import logger

# Forward references
if TYPE_CHECKING:
    from silex_client.graph.command import Command


class CommandQuery:
    """
    Used to manipulate and execute commands
    """
    
    def __init__(self, command: Command):
        self.command = command

    def set_parameter(self, parameter_name: str, new_value: Any):
        """
        Used to set a specific paramater
        """
        # Check if teh given parameter exists
        if parameter_name not in self.command.inputs:
            logger.error(
                f"Teh parameter : {parameter_name}, doesn't exist in this Command"
            )
            return

        # Chack if given value type corresponds to the socket type
        socket = self.command.inputs[parameter_name]
        if type(new_value) != type(socket.value):
            logger.error(
                f"Wrong type was given : {type(new_value)} instead of {type(socket.value)}"
            )
            return

        # Modify socket value and set parameter
        socket.value = new_value
        self.command.inputs[parameter_name] = socket

    def exectue(self):
        pass    
        


