from silex_dcc.utils.config import Config


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
            "task": "fx",
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

        pre_action = []
        action = []
        post_action = []

        return [pre_action, action, post_action]

    def execute_action(self, action_name):
        """
        Create and execute a list of modules according to
        the given action name and the context data
        """
        pre_action, action, post_action = self.get_action(action_name)


context = Context()
