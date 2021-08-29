from silex_client.utils.context import Context
from silex_client.utils.log import logger

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

    action = context.get_action(action_name)

    for set_parameter in kwargs.get("set_parameters", []):
        set_parameter = set_parameter.replace(" ", "")
        if "=" not in set_parameter:
            logger.error("Invalid set parameter string, it must follow the schema: <path> = <value>")
        parameter_path = set_parameter.split("=")[0]
        parameter_value = set_parameter.split("=")[1]
        action.set_parameter(parameter_path, parameter_value)
    action.execute()

def command_handler(command_name: str, **kwargs) -> None:
    """
    Execute the given command in the current context
    """
    if kwargs.get("list", False):
        # Just print the available actions
        print("Available commands  :")
