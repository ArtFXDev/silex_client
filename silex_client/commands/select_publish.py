from __future__ import annotations

import typing
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import SelectParameterMeta
from silex_client.resolve.config import Config

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class SelectPublish(CommandBase):
    """
    Put the given file on database and to locked file system
    """

    parameters = {
        "publish_type": {
            "label": "Select a publish type",
            "type": SelectParameterMeta(
                [publish_action["name"] for publish_action in Config().publishes]
            ),
            "value": None,
            "tooltip": "Select a publish type in the list",
        },
    }

    required_metadata = ["project"]

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        print(parameters["publish_type"])

        publish_action = Config().resolve_publish(parameters["publish_type"])
        print(publish_action)
