"""
@author: TD gang

Entry point for the CLI tools of silex
"""

import argparse
from typing import Callable, Dict, Optional

from silex_client.cli import handlers


def main(handlers_mapping: Optional[Dict[str, Callable]] = None):
    """
    Parse the given arguments and call the appropriate handlers
    """
    HANDLERS_MAPPING = {
        "action": handlers.action_handler,
        "command": handlers.command_handler,
        "launch": handlers.launch_handler,
    }
    if handlers_mapping:
        HANDLERS_MAPPING.update(handlers_mapping)

    context_parser = argparse.ArgumentParser(add_help=False)
    context_parser.add_argument(
        "--task-id",
        "-t",
        help="Specify the ID of the task you can the set the context in",
        dest="task_id",
        type=str,
    )

    execution_parser = argparse.ArgumentParser(add_help=False)
    execution_parser.add_argument(
        "--list",
        "-l",
        default=False,
        help="List the available options for the subcommand in the context",
        action="store_true",
    )

    parser = argparse.ArgumentParser(
        prog="silex", description="CLI for the silex pipeline ecosystem"
    )
    subparsers = parser.add_subparsers(
        help="The action to perform under the given context", dest="subcommand"
    )

    action_parser = subparsers.add_parser(
        "action",
        help="Execute the given action in the context",
        parents=[execution_parser, context_parser],
    )
    command_parser = subparsers.add_parser(
        "command",
        help="Execute the given command in the context",
        parents=[execution_parser, context_parser],
    )
    launcher_parser = subparsers.add_parser(
        "launch",
        help="Launch the given program in the context",
        parents=[context_parser],
    )

    action_parser.add_argument(
        "action_name",
        help="The name of the action to perform under the context",
        default=None,
        nargs="?",
    )
    action_parser.add_argument(
        "--list-parameters",
        "-lp",
        help="Print the parameters of the selected action",
        default=False,
        action="store_true",
        dest="list_parameters",
    )
    action_parser.add_argument(
        "--parameter",
        "-p",
        help="Set the parameters value with <path> = <value>",
        dest="set_parameters",
        action="append",
        default=[],
    )
    action_parser.add_argument(
        "--batch",
        "-b",
        help="The action will run without prompting input from user",
        default=False,
        action="store_true",
        dest="batch",
    )
    action_parser.add_argument(
        "--simplify",
        "-s",
        help="Execute the action in simplify mode",
        default=False,
        action="store_true",
        dest="simplify",
    )
    action_parser.add_argument(
        "--category",
        "-c",
        help="The category the action belong to",
        default="action",
        dest="category",
    )

    command_parser.add_argument(
        "command_name",
        help="The python path of the command to perform under the context",
        default=None,
        nargs="?",
    )

    launcher_parser.add_argument(
        "dcc",
        help="The dcc to start",
        default=None,
        nargs="?",
    )

    launcher_parser.add_argument(
        "--file",
        "-f",
        help="The file to open within the dcc",
        type=str,
        required=False,
    )
    launcher_parser.add_argument(
        "--action",
        "-a",
        help="the action we want to execute when file open",
        type=str,
        required=False,
    )
    launcher_parser.add_argument(
        "--command",
        "-cm",
        help="the command to execute when the file open",
        type=str,
        required=False,
    )

    args = vars(parser.parse_args())

    subcommand = args.pop("subcommand", None)
    if subcommand is not None:
        # Execute the appropriate handler according to the subparser
        HANDLERS_MAPPING[subcommand](**args)


if __name__ == "__main__":
    main()
