"""
@author: TD gang

Defintion of the handlers for all the CLI commands
"""

import asyncio
import os
import pprint
import subprocess
from concurrent import futures

import gazu.files
from silex_client.action.action_query import ActionQuery
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.authentification import authentificate_gazu
from silex_client.utils.log import logger


def action_handler(action_name: str, **kwargs) -> None:
    """
    Execute the given action in the resolved context
    """
    if kwargs.get("list", False):
        # Just print the available actions
        action_names = [action["name"] for action in Config.get().actions]
        print("Available actions :")
        pprint.pprint(action_names)
        return

    if not action_name:
        logger.error("No action name provided")
        return

    if kwargs.get("task_id") is not None:
        os.environ["SILEX_TASK_ID"] = kwargs["task_id"]

    category = kwargs.get("category", "action")

    silex_context = Context.get()
    silex_context.start_services()

    action = ActionQuery(
        action_name, category=category, simplify=kwargs.get("simplify", False)
    )
    if not action.commands:
        logger.error("The resolved action is invalid")
        return

    if kwargs.get("list_parameters", False):
        # Just print the available actions
        parameters = action.parameters
        print(f"Parameters for action {action_name} :")
        pprint.pprint(parameters)
        return

    for set_parameter in kwargs.get("set_parameters", []):
        set_parameter = set_parameter.replace(" ", "")
        if "=" not in set_parameter:
            logger.error(
                "Invalid set parameter string, it must follow the schema: <path> = <value>"
            )
        parameter_path = set_parameter.split("=")[0]
        parameter_value = set_parameter.split("=")[1]
        action.set_parameter(parameter_path, parameter_value)

    try:
        action_future = action.execute(batch=kwargs.get("batch", False))
        if not kwargs.get("batch", False):
            action_future = action.closed
        while not action_future.done():
            futures.wait([action_future], timeout=0.05)
            while not Context.get().callback_queue.empty():
                Context.get().callback_queue.get()()
    except KeyboardInterrupt:
        action.cancel()
    finally:
        futures.wait([silex_context.ws_connection.stop()], timeout=None)
        silex_context.event_loop.stop()


def command_handler(command_name: str, **kwargs) -> None:
    """
    Execute the given command in the current context
    """
    if kwargs.get("list", False):
        # Just print the available actions
        print("Available commands  :")
        return

    raise NotImplementedError("This feature is still WIP")


def launch_handler(dcc: str, **kwargs) -> None:
    """
    Run the given command in the selected context
    """
    if not authentificate_gazu():
        raise Exception(
            "Could not connect to the zou database, please connect to your account with silex"
        )

    softwares = asyncio.run(gazu.files.all_softwares())
    if not dcc in [software["short_name"] for software in softwares]:
        logger.error(
            "Could not launch the given dcc: The selected dcc %s does not exists", dcc
        )
        return

    command = [dcc]
    args_list = []


    if kwargs.get("task_id") is not None:
        os.environ["SILEX_TASK_ID"] = kwargs["task_id"]

    if kwargs.get("file") is not None:
        command.append(kwargs["file"])

    # check for env variable
    if os.environ.get("SILEX_DCC_BIN") is not None:
        command.pop(0)
        args_list = [os.environ["SILEX_DCC_BIN"]]

    additional_args = os.environ.get("SILEX_DCC_BIN_ARGS")
    if additional_args is not None:
        args_list.extend(additional_args.split(" "))

    new_command = args_list + command

    subprocess.Popen(new_command, cwd=os.getcwd(), shell=True)
