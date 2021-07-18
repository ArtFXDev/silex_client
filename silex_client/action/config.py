"""
@author: TD gang

Utility class that lazy load and resolve the configurations on demand
"""

import os
from typing import Dict, Any

import yaml

from silex_client.utils.log import logger
from silex_client.action.loader import Loader


class Config():
    """
    Utility class that lazy load and resolve the configurations on demand
    """
    def __init__(self, config_root_path=None, default_config=None):
        # Initialize the root of all the config files
        if not config_root_path:
            config_root_path = os.getenv("SILEX_CLIENT_CONFIG", None)
            if config_root_path is None:
                logger.error("Config root path not found")

        # Initialize the name of the default config file
        self.default_config = default_config

    def resolve_config(self, action_name: str, **kwargs: Dict[str, Any]):
        """
        Resolve a config file from its name by looking in the stored root path
        """
        # Find the config file
        # TODO: Get the config root location from the kwargs
        dirname = os.path.dirname(__file__)
        config_root = os.path.abspath(
            os.path.join(dirname, "..", "..", "config", "action"))
        try:
            config_file = next(
                file for file in os.listdir(config_root)
                if os.path.splitext(file)[0] == action_name
                and os.path.splitext(file)[1] in [".yaml", ".yml"])
        except (StopIteration, FileNotFoundError):
            logger.error("Could not find config file for action %s" %
                         action_name)
            return
        config_path = os.path.join(config_root, config_file)

        # Load the config
        config = {}
        with open(config_path, "r") as config_data:
            config_yaml = yaml.load(config_data, Loader)
            config = config_yaml

        return config
