from silex_client.utils.context import Context

import pprint

def action_handler(action_name: str, list_actions: bool=False) -> None:
    """
    Execute the given action in the current context
    """

    context = Context.get()
    if list_actions:
        # Just print the available actions
        print("Available actions :")
        action_names = [action["name"] for action in context.config.actions]
        pprint.pprint(action_names)
        return

    context.get_action(action_name).execute()
