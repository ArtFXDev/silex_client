from rez import resolved_context

from silex_client.utils.context import Context
from silex_client.utils.log import logger

import pprint

def resolve_rez_context(**kwargs) -> resolved_context.ResolvedContext:
    """
    Resolve a rez context and apply it to the current python session
    """
    PACKAGES = ["dcc"]
    EPHEMERALS = ["project", "asset", "sequence", "shot", "task"]

    packages = []
    for package in PACKAGES:
        version = kwargs.get(package)
        if not version:
            continue
        packages.append(f"{packages}-=={version}")

    for ephemeral in EPHEMERALS:
        version = kwargs.get(ephemeral)
        if not version:
            continue
        # TODO: Check if the entity exists in the database
        packages.append(f".{ephemeral}-=={version}")
        
    context = resolved_context.ResolvedContext(packages)
    context.apply()
    return context
    
def shell_handler(**kwargs) -> None:
    """
    Execute a shell in the resolved context
    """
    rez_context = resolve_rez_context(**kwargs)
    context = Context.get()
    context.rez_context = rez_context
    rez_context.execute_shell()

def action_handler(action_name: str, **kwargs) -> None:
    """
    Execute the given action in the resolved context
    """
    rez_context = resolve_rez_context(**kwargs)
    context = Context.get()
    context.rez_context = rez_context
    if kwargs.get("list", False):
        # Just print the available actions
        action_names = [action["name"] for action in context.config.actions]
        print("Available actions :")
        pprint.pprint(action_names)
        return

    if not action_name:
        logger.error("No action name provided")
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
