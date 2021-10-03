import pprint

from silex_client.utils import context
from silex_client.utils.log import logger


def action_handler(action_name: str, **kwargs) -> None:
    """
    Execute the given action in the resolved context
    """
    silex_context = context.Context.get()
    if not silex_context.is_valid:
        logger.error(
            "Could not execute the action %s: The silex context is invalid", action_name
        )
        return

    if kwargs.get("list", False):
        # Just print the available actions
        action_names = [action["name"] for action in silex_context.config.actions]
        print("Available actions :")
        pprint.pprint(action_names)
        return

    if not action_name:
        logger.error("No action name provided")
        return

    if kwargs.get("list_parameters", False):
        # Just print the available actions
        parameters = silex_context.get_action(action_name).parameters
        print(f"Parameters for action {action_name} :")
        pprint.pprint(parameters)
        return

    action = silex_context.get_action(action_name)

    for set_parameter in kwargs.get("set_parameters", []):
        set_parameter = set_parameter.replace(" ", "")
        if "=" not in set_parameter:
            logger.error(
                "Invalid set parameter string, it must follow the schema: <path> = <value>"
            )
        parameter_path = set_parameter.split("=")[0]
        parameter_value = set_parameter.split("=")[1]
        action.set_parameter(parameter_path, parameter_value)
    action.execute()


def command_handler(command_name: str, **kwargs) -> None:
    """
    Execute the given command in the current context
    """
    silex_context = context.Context.get()
    if not silex_context.is_valid:
        logger.error(
            "Could not execute the command %s: The silex context is invalid",
            command_name,
        )
        return

    if kwargs.get("list", False):
        # Just print the available actions
        print("Available commands  :")
        return

    raise NotImplementedError("This feature is still WIP")
