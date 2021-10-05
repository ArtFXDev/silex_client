"""
@author: TD gang

Entry point for the CLI tools of silex
"""

import argparse

from silex_client.cli import handlers


def main():
    """
    Parse the given arguments and call the appropriate handlers
    """
    HANDLERS_MAPPING = {
        "action": handlers.action_handler,
        "command": handlers.command_handler,
    }
    
    context_parser = argparse.ArgumentParser(add_help=False)
    context_parser.add_argument(
        "--task-id",
        "-t",
        help="Specify the ID of the task you can the set the context in",
        type=int
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

    command_parser.add_argument(
        "command_name",
        help="The python path of the command to perform under the context",
        default=None,
        nargs="?",
    )

    launcher_parser.add_argument(
            "--command",
            "-c",
            help="The command to execute in the context",
            type=str
        )

    args = vars(parser.parse_args())

    context = args.pop("context", None)
    if context is not None:
        # Resolve the context
        pass

    subcommand = args.pop("subcommand", None)
    if subcommand is not None:
        # Execute the appropriate handler according to the subparser
        HANDLERS_MAPPING[subcommand](**args)


if __name__ == "__main__":
    main()
