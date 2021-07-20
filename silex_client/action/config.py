"""
@author: TD gang

Utility class that lazy load and resolve the configurations on demand
"""

import os
import copy
import importlib
from typing import Dict, List, Union, Any

from silex_client.utils.log import logger
from silex_client.action.loader import Loader


class Config():
    """
    Utility class that lazy load and resolve the configurations on demand
    """
    def __init__(self, config_search_path: Union[List[str], str] = None):
        # List of the path to look for any included file
        self.config_search_path = ["/"]

        # Add the custom config search path
        if config_search_path is not None:
            if isinstance(config_search_path, str):
                self.config_search_path.append(config_search_path)
            else:
                self.config_search_path += config_search_path

        # Look for config search path in the environment variables
        env_config_path = os.getenv("SILEX_CLIENT_CONFIG", None)
        if env_config_path is not None:
            self.config_search_path += env_config_path.split(os.pathsep)

        # Add the config folder of this repo to the config search path
        repo_root = importlib.import_module("silex_client")
        repo_dir = os.path.dirname(repo_root.__file__)
        repo_config = os.path.abspath(
            os.path.join(repo_dir, "..", "config", "action"))
        self.config_search_path.append(repo_config)

    def resolve_action(self, action_name: str, **kwargs: Dict) -> Any:
        """
        Resolve a config file from its name by looking in the stored root path
        """
        # TODO: Add some search path according to the given kwargs
        search_path = copy.deepcopy(self.config_search_path)
        # Find the file in the list of search path
        config_path = None
        for path in search_path:
            try:
                config_file = next(
                    file for file in os.listdir(path)
                    if os.path.splitext(file)[0] == action_name
                    and os.path.splitext(file)[1] in [".yaml", ".yml"])

                config_path = os.path.abspath(os.path.join(path, config_file))
                logger.debug("Found action config at %s", config_path)
                break
            except StopIteration:
                continue

        if config_path is None:
            logger.error("Could not resolve config for the action %s",
                         action_name)
            return None

        # Load the config
        with open(config_path, "r") as config_data:
            loader = Loader(config_data, tuple(search_path))
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()
