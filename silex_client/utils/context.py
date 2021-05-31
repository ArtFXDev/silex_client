import importlib

from silex_client.utils.config import Config


class Context:
    """
    Singleton like class that keeps track of the current context
    """

    _metadata = {}

    def __init__(self):
        self.config = Config()

    @property
    def metadata(self):
        # TODO: Check if the context is outdated and update it automaticaly if it is
        # Lazy load the context's metadata
        if self._metadata == {}:
            self._metadata = {
                "dcc": "maya",
                "task": "modeling",
                "project": "TEST_PIPE",
                "user": "slambin",
                "entity": "shot",
                "sequence": 50,
                "shot": 120,
            }

        return self._metadata

    @metadata.setter
    def metadata(self, data):
        self._metadata = data

    def update_metadata(self, data):
        self._metadata.update(data)

    def get_action(self, action_name):
        """
        Return a list of modules to execute for an action
        """

        config_metadata = self.metadata
        config_metadata["action"] = action_name
        action = self.config.resolve_config(**config_metadata)

        return action

    def execute_action(self, action_name):
        """
        Create and execute a list of modules according to
        the given action name and the context data
        """
        action = self.get_action(action_name)
        for key, item in action.items():
            for command in item:
                # Skip in no module path is given
                if "command" not in command:
                    continue
                # Import the given module
                split = command["command"].split(".")
                package = importlib.import_module(
                    f"silex_client.{command['command'].replace('.' + split[-1], '')}"
                )
                module = getattr(package, split[-1])

                # If some parameters where given pass them when calling the module
                if "parm" in command:
                    module(**(command["parm"]))
                else:
                    module()


context = Context()
