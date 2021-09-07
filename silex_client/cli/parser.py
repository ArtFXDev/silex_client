from silex_client.cli import handlers

import argparse

def main():
    """
    Parse the given arguments and call the appropriate handlers
    """
    HANDLERS_MAPPING = {"shell": handlers.shell_handler, "action": handlers.action_handler, "command": handlers.command_handler}
    
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--list", "-l", default=False, help="List the available options for the subcommand in the context", action="store_true")
    parent_parser.add_argument("--project", "-pr", type=str, dest="project", help="The name of the project")
    parent_parser.add_argument("--asset", "-as", type=str, dest="asset", help="The name of the asset")
    parent_parser.add_argument("--sequence", "-sq", type=int, dest="sequence", help="The index of the sequence")
    parent_parser.add_argument("--shot", "-sh", type=int, dest="shot", help="The index of the shot")
    parent_parser.add_argument("--task", "-ta", type=str, dest="task", help="The name of the task")

    parser = argparse.ArgumentParser(prog="silex", description="CLI for the silex pipeline ecosystem")
    subparsers = parser.add_subparsers(help="The action to perform under the given context", dest="subcommand")

    shell_parser = subparsers.add_parser("shell", help="Execute a shell in the context", parents=[parent_parser])
    action_parser = subparsers.add_parser("action", help="Execute the given action in the context", parents=[parent_parser])
    command_parser = subparsers.add_parser("command", help="Execute the given command in the context", parents=[parent_parser])

    action_parser.add_argument("action_name", help="The name of the action to perform under the context", default=None, nargs="?")
    action_parser.add_argument("--list-parameters", "-lp", help="Print the parameters of the selected action", default=False, action="store_true", dest="list_parameters")
    action_parser.add_argument("--parameter", "-p", help="Set the parameters value with <path> = <value>", dest="set_parameters", action="append", default=[])

    command_parser.add_argument("command_name", help="The python path of the command to perform under the context", default=None, nargs="?")

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
