from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
import copy
import contextlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pkg_resources import iter_entry_points, DistributionNotFound

from silex_client.resolve.yaml_loader import YAMLLoader
from silex_client.utils.log import logger


class YAMLResolver(ABC):
    """
    Utility class that lazy load and resolve yaml configuration
    This class is meant to be inherited from
    """

    CONFIG_ENV = "NONE"
    CONFIG_ENTRY_PONT = "NONE"
    CONFIG_ENABLE_CACHE_ENV = "NONE"

    NAMESPACE_SEP = "::"

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or self.get_default_search_paths()
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self.enable_cache = bool(os.getenv(self.CONFIG_ENABLE_CACHE_ENV))

    @classmethod
    def split_namespace(cls, name: str) -> Tuple[List[str], str]:
        splitted_namespace = name.split(cls.NAMESPACE_SEP)
        return splitted_namespace[:-1], splitted_namespace[-1]

    def get_namespace(
        self, path: Path, search_paths: Optional[List[Path]] = None
    ) -> str:
        for search_path in search_paths or self.search_paths:
            with contextlib.suppress(ValueError):
                relative_path = path.relative_to(search_path).with_suffix("")
                return self.NAMESPACE_SEP.join(relative_path.parts)

        return ""

    def get_child_paths(
        self, path: Path, search_paths: List[Path] = None
    ) -> List[Path]:
        search_paths = search_paths or self.search_paths
        for index, search_path in enumerate(search_paths):
            with contextlib.suppress(ValueError):
                path.relative_to(search_path)
                return search_paths[index:]

        return []

    def find_configs(self, name: str, search_paths: List[Path] = None) -> List[Path]:
        """
        Find the all the yaml with the specified name in the search paths
        They are returned in the order they are found.
        """
        configs: List[Path] = []
        namespaces, name = self.split_namespace(name)
        for path in search_paths or self.search_paths:
            for namespace in namespaces:
                path = path / namespace

            if not path.exists() or not path.is_dir():
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
        found_configs = self.find_configs(name, search_paths)
        return found_configs[0] if found_configs else None

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
            for config_path in path.rglob("*.yml"):
                configs[config_path.stem].append(config_path)
            for config_path in path.rglob("*.yaml"):
                configs[config_path.stem].append(config_path)

        return configs

    def resolve_config(
        self,
        name: str,
        search_paths: Optional[List[Path]] = None,
        traceback: List[Path] = None,
    ) -> Optional[dict]:
        """
        Resolve a config file from its name and return the resulting dict
        """
        traceback = traceback or []
        if name in self._config_cache and self.enable_cache:
            return self._config_cache[name]

        search_paths = search_paths or self.search_paths
        config_path = self.find_config(name, search_paths)

        if config_path is None:
            return None

        # The traceback keeps track of all the inherited actions
        # it is used to track infinite loops
        if config_path in traceback:
            formatted_traceback = "\n - " + "\n - ".join(
                [str(path) for path in [*traceback, config_path]]
            )
            raise RecursionError(f"Infinite inheriance detected: {formatted_traceback}")

        traceback.append(config_path)

        # A config cannot inherit/insert data from an other config that is above
        # itself in the searchs path list
        inheritance_paths = self.get_child_paths(config_path, search_paths)
        resolved_config = self.load_config(config_path, inheritance_paths, traceback)

        if self.enable_cache and resolved_config is not None:
            self._config_cache[name] = resolved_config

        return resolved_config

    def load_config(
        self, config_path: Path, search_paths: List[Path], traceback: List[Path]
    ) -> Any:
        with open(config_path, "r", encoding="utf-8") as config_data:
            resolver = copy.deepcopy(self)
            resolver.search_paths = search_paths
            loader = YAMLLoader(config_data, config_path, resolver, traceback)
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
        for entry_point in iter_entry_points(self.CONFIG_ENTRY_PONT):
            with contextlib.suppress(DistributionNotFound, ModuleNotFoundError):
                action_search_path += entry_point.load()

        return action_search_path

    @staticmethod
    @abstractmethod
    def get():
        pass
