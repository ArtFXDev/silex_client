from __future__ import annotations

import logging
import math
import typing
from typing import Any, Dict

import gazu
import gazu.client
from silex_client.action.command_base import CommandBase

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class AddSilexCoinsCommand(CommandBase):
    """
    Add some Silex coins for the logged in user
    """

    parameters = {
        "amount": {"hide": True, "type": int, "value": 1},
        "count_commands": {"hide": True, "type": bool, "value": False},
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if action_query.batch:
            return

        if parameters["amount"] == 0:
            return

        # It means we already gave some coins
        if action_query.store.get("silexCoins", False):
            return

        current_user = await gazu.client.get_current_user()

        if "coins" not in current_user:
            return

        new_coins_amount = current_user["coins"] + parameters["amount"]

        if parameters["count_commands"]:
            new_coins_amount += math.floor(len(action_query.commands) / 70)

        await gazu.raw.put(
            f"data/persons/{current_user['id']}",
            {"coins": new_coins_amount},
        )

        await action_query.ws_connection.async_send(
            "/front-event",
            "frontEvent",
            {
                "data": {
                    "type": "silexCoins",
                    "data": {"new_coins": new_coins_amount},
                }
            },
        )

        action_query.store["silexCoins"] = True
