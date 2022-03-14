from silex_client.utils import farm

import tractor.api.author as author


def dirmap(path: str) -> str:
    """Returns a string that needs to be formatted with the Dirmap in Tractor"""
    return f"%D({path})"


def convert_to_tractor_command(command: farm.Command) -> author.Command:
    """
    Converts a generic Command to a Tractor Command instance
    """
    return author.Command(
        argv=command.argv,
        # Run commands on the same host
        samehost=1,
        # Limit tags with rez packages
        # Useful when limiting the amout of vray jobs on the farm for example
        tags=command.tags,
    )


def convert_to_tractor_task(task: farm.Task) -> author.Task:
    """
    Converts a generic Task to a Tractor Task instance
    """
    tractor_task = author.Task(title=task.title)

    # Convert commands
    for command in task.commands:
        tractor_task.addCommand(convert_to_tractor_command(command))

    # Recursively convert children tasks
    for child in task.children:
        tractor_task.addChild(convert_to_tractor_task(child))

    return tractor_task
