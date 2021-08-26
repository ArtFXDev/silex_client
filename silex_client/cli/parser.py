import argparse

def main():
    """
    Parse the given arguments and call the appropriate handlers
    """
    parser = argparse.ArgumentParser(prog="silex", description="CLI for the silex pipeline ecosystem")
    parser.add_argument('--context', type=str, help="Resolve and open an environment in the given context")
    parser.add_argument('--dcc', type=str, help="Start the given DCC in the selected context or in the current one")
    parser.add_argument('--action', type=str, help="Execute the given action in the selected context or in the current one")
    parser.add_argument('--command', type=str, help="Execute the given command in the selected context or in the current one")
    args = parser.parse_args()

if __name__ == "__main__":
    main()
