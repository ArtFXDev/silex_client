import argparse

def main():
    """
    Parse the given arguments and call the appropriate handlers
    """
    parser = argparse.ArgumentParser(prog="silex", description="CLI for the silex pipeline ecosystem")
    parser.add_argument('--context', type=str, help="Resolve and open an environment in the given context", dest="context")
    parser.add_argument("--list", "-l", default=False, help="List the available options for the subcommand in the context", action="store_true")
    subparsers = parser.add_subparsers(help="The action to perform under the given context", dest="subcommand")

    action_parser = subparsers.add_parser("action", help="Execute the given action in the context")
    command_parser = subparsers.add_parser("command", help="Execute the given command in the context")

    action_parser.add_argument("action_name", help="The name of the action to perform under the context")

    command_parser.add_argument("command_name", help="The python path of the command to perform under the context")

    args = parser.parse_args()

    print(args)

if __name__ == "__main__":
    main()
