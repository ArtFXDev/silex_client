import uuid

from silex_client.network.websocket import WebsocketConnection


class ActionBuffer():
    """
    Store the state of an action, it is used as a comunication entry with the UI
    """
    def __init__(self, ws_connection: WebsocketConnection):
        self.ws_connection = ws_connection
        self.uid = uuid.uuid1()

        self._parameters = {}
        self._variables = {}
        self._commands = {}

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
        # TODO: Check if the given commands are correct
        self._commands.update(commands)
