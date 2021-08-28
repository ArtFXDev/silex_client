from silex_client.utils.context import Context

import pprint

def action_handler(action_name: str, **kwargs) -> None:
    """
    Execute the given action in the current context
    """
    context = Context.get()
    if kwargs.get("list", False):
        # Just print the available actions
        print("Available actions :")
        action_names = [action["name"] for action in context.config.actions]
        pprint.pprint(action_names)
        return

    context.get_action(action_name).execute()

def command_handler(command_name: str, **kwargs) -> None:
    """
    Execute the given command in the current context
    """
    if kwargs.get("list", False):
        # Just print the available actions
        print("Available commands  :")
