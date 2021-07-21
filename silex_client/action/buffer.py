import uuid

from silex_client.network.websocket import WebsocketConnection
from silex_client.utils.merge import merge_data
from silex_client.utils.log import logger


class ActionBuffer():
    """
    Store the state of an action, it is used as a comunication entry with the UI
    """

    COMMANDS_TEMPLATE = {"pre_action": [], "action": [], "post_action": []}
    COMMAND_TEMPLATE = {"command": "", "name": ""}

    def __init__(self, ws_connection: WebsocketConnection):
        self.ws_connection = ws_connection
        self.uid = uuid.uuid1()

        self._parameters = {}
        self._variables = {}
        self._commands = {"pre_action": [], "action": [], "post_action": []}

    def _serialize(self):
        """
        Convert the action's data into json so it can be sent to the UI
        """
        pass

    def _deserialize(self, serealised_data):
        """
        Convert back the action's data from json into this object
        """
        pass

    def send(self):
        """
        Serialize and send this buffer to the UI though websockets
        """
        pass

    def receive(self, timeout: int):
        """
        Wait for the UI to send back a buffer and deserialize it
        """
        pass

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict):
        # TODO: Check if the given parameters are correct
        self._parameters.update(parameters)

    @property
    def variables(self):
        return self._variables

    @variables.setter
    def variables(self, variables: dict):
        # TODO: Check if the given variables are correct
        self._variables.update(variables)

    @property
    def commands(self):
        return self._commands

    @commands.setter
    def commands(self, commands: dict):
        # Check if the commands are valid
        filtered_commands = self.COMMANDS_TEMPLATE
        for step in self.COMMANDS_TEMPLATE.keys():
            for command in commands.get(step, []):
                # Check if the command has the required keys
                if not all(key in command.keys()
                           for key in self.COMMAND_TEMPLATE):
                    logger.warning("Invalid command %s", command)
                    continue
                # Append validated command
                filtered_commands[step].append(command)

        # Override the data that has the same name and append the new names
        self._commands = merge_data(filtered_commands, self.commands)
