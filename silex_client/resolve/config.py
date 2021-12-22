"""
@author: TD gang

Utility class that will find the configurations according to the environment variables
SILEX_ACTION_CONFIG: For the actions
"""

from __future__ import annotations
import copy
import contextlib
import os
import sys
import pkg_resources
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        config_search_path: search_path = None,
    ):
        # Add the custom action config search path
        if config_search_path is not None:
            self.action_search_path = config_search_path
            return

    @staticmethod
    def get() -> Config:
        """
        Return a globaly instanciated config. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "config")

    def find_config(self, search_path: List[str]) -> List[Dict[str, str]]:
        """
        Find all the configs in the given paths
        """
        found_actions = []

        for path in search_path:
            if not os.path.isdir(path):
                continue
            for file_path in os.listdir(path):
                split_path = os.path.splitext(file_path)
                if split_path[0] in [action["name"] for action in found_actions]:
                    continue
                if split_path[1] in [".yaml", ".yml"]:
                    action_path = os.path.abspath(os.path.join(path, file_path))
                    found_actions.append({"name": split_path[0], "path": action_path})

        return found_actions

    def get_actions(self, category: str = "action") -> List[Dict[str, str]]:
        """
        List of all the available actions config found in the given category
        """
        return self.find_config(
            [os.path.join(path, category) for path in self.action_search_path]
        )

    @property
    def actions(self) -> List[Dict[str, str]]:
        return self.get_actions("action")

    @property
    def publishes(self) -> List[Dict[str, str]]:
        return self.get_actions("publish")

    @property
    def conforms(self) -> List[Dict[str, str]]:
        return self.get_actions("conform")

    @property
    def submits(self) -> List[Dict[str, str]]:
        return self.get_actions("submit")

    def resolve_config(
        self,
        action_name: str,
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
        self, action_name: str, category: str = "action"
    ) -> Optional[dict]:
        return self.resolve_config(action_name, self.get_actions(category))

    def resolve_publish(self, action_name: str) -> Optional[dict]:
        return self.resolve_action(action_name, "publish")

    def resolve_conform(self, action_name: str) -> Optional[dict]:
        return self.resolve_action(action_name, "conform")

    def resolve_submit(self, action_name: str) -> Optional[dict]:
        return self.resolve_action(action_name, "submit")

    def _load_config(self, config_path: str) -> Any:
        # Load the config
        with open(config_path, "r", encoding="utf-8") as config_data:
            search_path = copy.deepcopy(self.action_search_path)
            search_path = [Path(path) for path in search_path]
            loader = Loader(config_data, Path(config_path), search_path)
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()

def get_action_search_path():
    """
    Get a list of search path from environment variables and entry points
    This is for the default Config object
    """
    action_search_path = []

    # Look for config search path in the environment variables
    env_config_path = os.getenv("SILEX_ACTION_CONFIG")
    if env_config_path is not None:
        action_search_path += env_config_path.split(os.pathsep)

    # Look for config search path in silex_config entry_point
    for entry_point in pkg_resources.iter_entry_points("silex_action_config"):
        with contextlib.suppress(pkg_resources.DistributionNotFound):
            action_search_path += entry_point.load()

    return action_search_path

config = Config(get_action_search_path())
