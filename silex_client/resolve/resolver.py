from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
import copy
import contextlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pkg_resources

from silex_client.resolve.loader import Loader
from silex_client.utils.log import logger


class Resolver(ABC):
    """
    Utility class that lazy load and resolve yaml configuration
    This class is meant to be inherited from
    """

    CONFIG_ENV = "NONE"
    CONFIG_ENTRY_PONT = "NONE"

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or self.get_default_search_paths()

    def find_configs(
        self, name: str, search_paths: Optional[List[Path]] = None
    ) -> List[Path]:
        """
        Find the all the yaml with the specified name in the search paths
        They are returned in the order they are found.
        """
        configs: List[Path] = []
        for path in search_paths or self.search_paths:
            if not path.is_dir():
                continue
            for config_path in path.iterdir():
                if config_path.stem != name:
                    continue
                if config_path.suffix not in [".yaml", ".yml"]:
                    continue

                logger.debug("Found action config at %s", config_path)
                configs.append(config_path)
                break

        return configs

    def find_config(
        self, name: str, search_paths: Optional[List[Path]] = None
    ) -> Optional[Path]:
        """
        Find the first yaml with the specified name in the search paths
        """
        return self.find_configs(name, search_paths)[0]

    def get_configs(
        self, search_paths: Optional[List[Path]] = None
    ) -> Dict[str, List[Path]]:
        """
        Return all the available configs in the search paths
        """
        configs: Dict[str, List[Path]] = defaultdict(list)

        for path in search_paths or self.search_paths:
            if not path.is_dir():
                continue
            for config_path in path.iterdir():
                if config_path.suffix not in [".yaml", ".yml"]:
                    continue

                configs[config_path.stem].append(config_path)

        return configs

    def resolve_config(
        self, name: str, search_paths: Optional[List[Path]] = None
    ) -> Optional[dict]:
        """
        Resolve a config file from its name and return the resulting dict
        """
        config_path = self.find_config(name, search_paths)
        return self.load_config(config_path) if config_path is not None else None

    def load_config(self, config_path: Path) -> Any:
        with open(config_path, "r", encoding="utf-8") as config_data:
            search_paths = copy.deepcopy(self.search_paths)
            loader = Loader(config_data, config_path, search_paths)
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()

    def get_default_search_paths(self) -> List[Path]:
        """
        Get a list of search path from environment variables and entry points
        """
        action_search_path = []

        # Look for config search path in the environment variables
        env_config_path = os.getenv(self.CONFIG_ENV)
        if env_config_path is not None:
            action_search_path += env_config_path.split(os.pathsep)

        # Look for config search path in silex_config entry_point
        for entry_point in pkg_resources.iter_entry_points(self.CONFIG_ENTRY_PONT):
            with contextlib.suppress(pkg_resources.DistributionNotFound):
                action_search_path += entry_point.load()

        return action_search_path

    @staticmethod
    @abstractmethod
    def get():
        pass
