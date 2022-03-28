import uuid
from typing import Optional

from silex_client.utils import farm

import tractor.api.author as author


def dirmap(path: str) -> str:
    """Returns a string that needs to be formatted with the Dirmap in Tractor"""
    return f"%D({path})"


def convert_to_tractor_command(
    command: farm.Command, id: str, refersto: Optional[str]
) -> author.Command:
    """
    Converts a generic Command to a Tractor Command instance
    """

    args = {
        "argv": command.argv,
        "id": id,
        # Useful when limiting the amout of vray jobs on the farm for example
        "tags": command.tags,
    }

    # Refersto allows to execute a command on the same host as the previous one
    if refersto is not None:
        args["refersto"] = refersto

    return author.Command(**args)


def convert_to_tractor_task(task: farm.Task) -> author.Task:
    """
    Converts a generic Task to a Tractor Task instance
    """
    tractor_task = author.Task(title=task.title)

    previous_id = None

    # Convert commands
    for command in task.commands:
        command_id = str(uuid.uuid4())
        tractor_task.addCommand(
            convert_to_tractor_command(command, command_id, previous_id)
        )
        previous_id = command_id

    # Recursively convert children tasks
    for child in task.children:
        tractor_task.addChild(convert_to_tractor_task(child))

    return tractor_task
