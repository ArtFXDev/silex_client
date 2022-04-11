from __future__ import annotations

import sys

from silex_client.resolve.resolver import Resolver


class ActionResolver(Resolver):
    """
    Utility class that lazy load and resolve yaml configuration for actions
    """

    CONFIG_ENV = "SILEX_ACTION_CONFIG"
    CONFIG_ENTRY_PONT = "silex_action_config"

    @staticmethod
    def get() -> ActionResolver:
        """
        Return a globaly instanciated config. This static method is just for conveniance
        """
        # Get the instance of Context created in this same module
        return getattr(sys.modules[__name__], "action_resolver")


action_resolver = ActionResolver()
