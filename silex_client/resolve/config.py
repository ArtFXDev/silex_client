"""
@author: TD gang

Utility class that will find the configurations according to the environment variables
SILEX_ACTION_CONFIG: For the actions
"""

import copy
import os
from typing import Any, Union, Dict, List, Optional

from dacite import types

from silex_client.resolve.loader import Loader
from silex_client.resolve.config_types import ActionYAML
from silex_client.utils.log import logger

search_path = Optional[List[str]]


class Config:
    """
    Utility class that lazy load and resolve the configurations on demand

    :ivar action_search_path: List of path to look for config files. The order matters.
    """

    def __init__(
        self,
        action_search_path: search_path = None,
        publish_search_path: search_path = None,
    ):
        # List of the path to look for any included file
        self.action_search_path = ["/"]
        self.publish_search_path = ["/"]

        # Add the custom action config search path
        if action_search_path is not None:
            self.action_search_path += action_search_path

        # Look for config search path in the environment variables
        env_config_path = os.getenv("SILEX_ACTION_CONFIG")
        if env_config_path is not None:
            self.action_search_path += env_config_path.split(os.pathsep)

        # Add the custom config publish search path
        if publish_search_path is not None:
            self.publish_search_path += publish_search_path

        # Look for publish config search path in the environment variables
        publish_config_path = os.getenv("SILEX_PUBLISH_ACTION_CONFIG")
        if publish_config_path is not None:
            self.publish_search_path += publish_config_path.split(os.pathsep)

    def find_config(self, search_path: List[str]) -> List[Dict[str, str]]:
        """
        Find all the configs in the given paths
        """
        found_actions = []

        for path in search_path:
            for file_path in os.listdir(path):
                split_path = os.path.splitext(file_path)
                if os.path.splitext(file_path)[1] in [".yaml", ".yml"]:
                    action_path = os.path.abspath(os.path.join(path, file_path))
                    found_actions.append({"name": split_path[0], "path": action_path})

        return found_actions

    @property
    def actions(self) -> List[Dict[str, str]]:
        """
        List of all the available actions config found
        """
        return self.find_config(self.action_search_path)

    @property
    def publishes(self) -> List[Dict[str, str]]:
        """
        List of all the available actions config found
        """
        return self.find_config(self.publish_search_path)

    def resolve_config(
        self,
        action_name: str,
        context_metadata: Dict[str, Any],
        configs: List[Dict[str, str]],
    ) -> Optional[dict]:
        """
        Resolve a config file from its name by looking in the stored root path
        """
        # Find the action config
        if action_name not in [action["name"] for action in configs]:
            logger.error(
                "Could not resolve the action %s: The action does not exists",
                action_name,
            )
            return None

        config_path = next(
            action["path"] for action in configs if action["name"] == action_name
        )
        logger.debug("Found action config at %s", config_path)
        action_config = self._load_config(config_path)

        # Dynamic type checking
        if not types.is_instance(action_config, ActionYAML):
            logger.error(
                "Could not resolve the action %s: The schema is invalid",
                action_name,
            )
            return None

        return action_config

    def resolve_action(
        self, action_name: str, context_metadata: Dict[str, Any] = None
    ) -> Optional[dict]:
        if context_metadata is None:
            context_metadata = {}

        return self.resolve_config(action_name, context_metadata, self.actions)

    def resolve_publish(
        self, action_name: str, context_metadata: Dict[str, Any] = None
    ) -> Optional[dict]:
        if context_metadata is None:
            context_metadata = {}

        return self.resolve_config(action_name, context_metadata, self.publishes)

    def _load_config(self, config_path: str) -> Any:
        # Load the config
        with open(config_path, "r", encoding="utf-8") as config_data:
            search_path = copy.deepcopy(self.action_search_path)
            loader = Loader(config_data, tuple(search_path))
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()
