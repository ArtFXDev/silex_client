from __future__ import annotations

import contextlib
import os
from importlib.util import spec_from_file_location, module_from_spec
from importlib.machinery import SourceFileLoader
import inspect
from pathlib import Path
from typing import cast, List, Optional

from silex_client.resolve.resolver import Resolver


class SocketResolver(Resolver):
    """
    Utility class that lazy load socket types definitions
    """

    SEARCH_ENV = "SILEX_SOCKET_DECLARATION"
    SEARCH_ENTRY_PONT = "silex_socket_declaration"
    ENABLE_HOT_RELOAD_ENV = "SILEX_HOT_RELOAD_SOCKET"

    def __init__(self, search_paths: Optional[List[Path]] = None):
        super().__init__(search_paths)
        self.enable_hot_reload = bool(os.getenv(self.ENABLE_HOT_RELOAD_ENV))

    def resolve_definition(
        self,
        name: str,
        search_paths: Optional[List[Path]] = None,
    ) -> Optional[dict]:
        """
        Find and load the socket definition in the list of search paths
        The first occurence is returned
        """

        for path in search_paths or self.search_paths:
            spec = spec_from_file_location(name, path)

            if spec is None or spec.loader is None:
                continue

            module = module_from_spec(spec)
            loader = cast(SourceFileLoader, spec.loader)
            loader.exec_module(module)

            with contextlib.suppress(StopIteration):
                return next(
                    member
                    for member_name, member in inspect.getmembers(module)
                    if inspect.isclass(member) and member_name == name
                )

        return None
