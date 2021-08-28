from silex_client.cli import handlers

import argparse

def main():
    """
    Parse the given arguments and call the appropriate handlers
    """
    HANDLERS_MAPPING = {"action": handlers.action_handler, "command": handlers.command_handler}

    parser = argparse.ArgumentParser(prog="silex", description="CLI for the silex pipeline ecosystem")
    parser.add_argument('--context', type=str, help="Resolve and open an environment in the given context", dest="context")
    parser.add_argument("--list", "-l", default=False, help="List the available options for the subcommand in the context", action="store_true")
    subparsers = parser.add_subparsers(help="The action to perform under the given context", dest="subcommand")

    action_parser = subparsers.add_parser("action", help="Execute the given action in the context")
    command_parser = subparsers.add_parser("command", help="Execute the given command in the context")

    action_parser.add_argument("action_name", help="The name of the action to perform under the context", default=None, nargs="?")
    action_parser.add_argument("--list-parameters", help="Print the parameters of the selected action", default=False, action="store_true", dest="list_parameters")

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
