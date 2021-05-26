import os


class Config(dict):
    """
    Utility class that lazy load the configuration files on demand
    """

    def __init__(self):
        self.root_config = os.getenv("SILEX_DCC_CONFIG")
