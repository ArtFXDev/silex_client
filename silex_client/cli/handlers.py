from silex_client.utils.context import Context


def action_handler(action_name: str, list_actions: bool=False):
    """
    Execute the given action in the current context
    """

    context = Context.get()
    if list_actions:
        # Just print the available actions
        return
