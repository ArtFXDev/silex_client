from __future__ import annotations

from abc import ABC, abstractmethod
import contextlib
import os
from pathlib import Path
from typing import List, Optional
from pkg_resources import iter_entry_points, DistributionNotFound


class Resolver(ABC):
    """
    Utility class that lazy load and resolve declaration files
    This class is meant to be inherited from
    """

    SEARCH_ENV = "NONE"
    SEARCH_ENTRY_PONT = "NONE"

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or self.get_default_search_paths()

    def get_default_search_paths(self) -> List[Path]:
        """
        Get a list of search path from environment variables and entry points
        """
        action_search_path = []

        # Look for config search path in the environment variables
        env_config_path = os.getenv(self.SEARCH_ENV)
        if env_config_path is not None:
            action_search_path += env_config_path.split(os.pathsep)

        # Look for config search path in silex  entry points
        for entry_point in iter_entry_points(self.SEARCH_ENTRY_PONT):
            with contextlib.suppress(DistributionNotFound, ModuleNotFoundError):
                entry_point_path = entry_point.load()
                if entry_point_path not in action_search_path:
                    action_search_path += entry_point_path

        return action_search_path

    @staticmethod
    @abstractmethod
    def get():
        pass
