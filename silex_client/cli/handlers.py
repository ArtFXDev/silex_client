from silex_client.utils.context import Context

import pprint

def action_handler(action_name: str, **kwargs) -> None:
    """
    Execute the given action in the current context
    """
    context = Context.get()
    if kwargs.get("list", False):
        # Just print the available actions
        action_names = [action["name"] for action in context.config.actions]
        print("Available actions :")
        pprint.pprint(action_names)
        return

    if not action_name:
        return
    
    if kwargs.get("list_parameters", False):
        # Just print the available actions
        parameters = context.get_action(action_name).parameters
        print(f"Parameters for action {action_name} :")
        pprint.pprint(parameters)
        return

    context.get_action(action_name).execute()

def command_handler(command_name: str, **kwargs) -> None:
    """
    Execute the given command in the current context
    """
    if kwargs.get("list", False):
        # Just print the available actions
        print("Available commands  :")
