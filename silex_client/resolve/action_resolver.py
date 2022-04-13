from __future__ import annotations

import sys

from silex_client.resolve.yaml_resolver import YAMLResolver


class ActionResolver(YAMLResolver):
    """
    Utility class that lazy load and resolve yaml configuration for actions
    """

    CONFIG_ENV = "SILEX_ACTION_CONFIG"
    CONFIG_ENTRY_PONT = "silex_action_config"
    CONFIG_ENABLE_CACHE_ENV = "SILEX_ENABLE_ACTION_CACHE"

    @staticmethod
    def get() -> ActionResolver:
        """
        Return a globaly instanciated config. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "action_resolver")


action_resolver = ActionResolver()
