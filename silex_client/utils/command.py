from typing import Any, Dict, List, Optional, Union


class CommandBuilder:
    """
    Used to construct a command with arguments with the format: executable {-key=value}
    """

    def __init__(
        self, executable: str, rez_packages: List[str] = [], delimiter: Optional[str] = "="
    ):
        self.executable = executable
        self.rez_cmd = None
        self.params: Dict[str, Optional[Union[Any, List[Any]]]] = {}
        self.rez_packages = rez_packages
        self.delimiter = delimiter

    def param(self, key: str, value: Union[Any, List[Any]] = None):
        """
        Add a parameter to the command
        """
        self.params[key] = value
        return self

    def disable(self, keys: List[str], false_value: Union[int, bool] = 0):
        """
        Set multiple keys with a false value
        """
        for key in keys:
            self.param(key, false_value)
        return self

    def add_rez_package(self, package: str):
        """
        Add one rez package that will be added to the final command
        """
        self.rez_packages.append(package)

    def as_argv(self) -> List[str]:
        """
        Return the full command as a list of tokens (argv)
        """

        args = []

        for (key, value) in self.params.items():
            if value is not None:
                if self.delimiter is not None:
                    # In case of a -key=value parameter
                    args.append(f"-{key}{self.delimiter}{value}")
                else:
                    # If there's no delimiter we add the values with spaces
                    # eg: -frames 0 1 5
                    args.append(f"-{key}")
                    values = value if type(value) == list else [value]
                    args.extend(values)
            else:
                # We just add -key as a flag
                args.append(f"-{key}")

        command: List[str] = [self.executable] + args

        if self.rez_packages:
            command = ["rez", "env"] + self.rez_packages + ["--"] + command

        return command

    def __repr__(self) -> str:
        return " ".join(self.as_argv())
