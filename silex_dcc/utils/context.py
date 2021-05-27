from silex_dcc.utils.config import Config
import os


class Context:
    """
    Singleton like class that keeps track of the current context
    """

    _data = {}

    def __init__(self):
        self.config = Config()

    @property
    def data(self):
        self._data = {
            "dcc": "maya",
            "task": "modeling",
            "project": "TEST_PIPE",
            "user": "slambin",
            "entity": "shot",
            "sequence": 50,
            "shot": 120,
        }

        return self._data

    def get_action(self, action_name):
        """
        Return a list of modules to execute for an action
        """

        config_data = self.data
        config_data["action"] = action_name
        action = self.config.resolve_config(**config_data)

        return action

    def execute_action(self, action_name):
        """
        Create and execute a list of modules according to
        the given action name and the context data
        """
        action = self.get_action(action_name)


context = Context()
