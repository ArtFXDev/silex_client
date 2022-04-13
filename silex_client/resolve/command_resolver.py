from __future__ import annotations

import sys

from silex_client.resolve.yaml_resolver import YAMLResolver


class CommandResolver(YAMLResolver):
    """
    Utility class that lazy load and resolve yaml configuration for commands
    """

    CONFIG_ENV = "SILEX_COMMAND_CONFIG"
    CONFIG_ENTRY_PONT = "silex_command_config"
    CONFIG_ENABLE_CACHE_ENV = "SILEX_ENABLE_CONFIG_CACHE"

    @staticmethod
    def get() -> CommandResolver:
        """
        Return a globaly instanciated config. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "command_resolver")


command_resolver = CommandResolver()
