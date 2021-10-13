"""
@author: TD gang

Defintion of the handlers for all the CLI commands
"""

from concurrent import futures
import os
import pprint
import subprocess
from typing import Dict

import gazu.task
import gazu.shot

from silex_client.core import context
from silex_client.utils.log import logger


async def resolve_context(task_id: int) -> Dict[str, str]:
    """
    Guess all the context from the task id
    """
    resolved_context = {}
    try:
        task = await gazu.task.get_task(task_id)
    except ValueError:
        logger.error("Could not resolve the context: The task ID is invalid")
        return resolved_context

    resolved_context["task"] = task["name"]
    resolved_context["task_id"] = task["id"]
    resolved_context["task_type"] = task["task_type"]["name"]
    resolved_context["project"] = task["project"]["name"]
    resolved_context["project_id"] = task["project"]["id"]

    resolved_context["silex_entity_type"] = task["entity_type"]["name"].lower()

    if task["entity_type"]["name"].lower() == "shot":
        resolved_context["shot_id"] = task["entity"]["id"]
        resolved_context["shot"] = task["entity"]["name"]

        sequence = await gazu.shot.get_sequence(task["entity"]["parent_id"])
        resolved_context["sequence_id"] = sequence["id"]
        resolved_context["sequence"] = sequence["name"]

    else:
        resolved_context["asset_id"] = task["entity"]["id"]
        resolved_context["asset"] = task["entity"]["name"]

    return resolved_context


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

    if kwargs.get("task_id") is not None:
        context_future = silex_context.event_loop.register_task(
            resolve_context(kwargs["task_id"])
        )
        resolved_context = context_future.result()
        silex_context.initialize_metadata(resolved_context)

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

    try:
        action_future = action.execute()
        while not action_future.done():
            futures.wait([action_future], timeout=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        futures.wait([silex_context.ws_connection.stop()], timeout=None)
        silex_context.event_loop.stop()


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


def launch_handler(command: str, **kwargs) -> None:
    """
    Run the given command in the selected context
    """
    # TODO: Find a way to get the stdout in the terminal on windows
    p = subprocess.Popen(command, cwd=os.getcwd())
