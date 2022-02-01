import copy
from typing import Any, List, Optional, Tuple, Union


class CommandBuilder:
    """
    Used to construct a command with arguments
    """

    def __init__(
        self,
        executable: Optional[str] = None,
        rez_packages: List[str] = [],
        delimiter: Optional[str] = "=",
        dashes: str = "-",
    ):
        self.executable = executable
        self.rez_cmd = None
        self.params: List[Tuple[Optional[str], Any]] = []
        self.rez_packages = rez_packages

        # Configuration
        self.delimiter = delimiter
        self.dashes = dashes

    def param(self, key: Optional[str], value: Any = None, condition: bool = True):
        """
        Add a parameter to the command
        Ex: CommandBuilder("ls").param("l") -> "ls -l"
            CommandBuilder("ls", dashes="--", delimiter=" ").param("time", "access") -> "ls --time access"
        """
        if condition:
            self.params.append((key, value))
        return self

    def value(self, value: Any):
        """
        Add a single value to the command

        Examples:
            CommandBuilder("python").value("test.py") -> "python test.py"
        """
        self.param(None, value)
        return self

    def disable(self, keys: List[str], false_value: Union[int, bool] = 0):
        """
        Set multiple keys with a false value

        Examples:
            CommandBuilder("vray").disable(["display", "progressUseColor"]) -> "vray -display=0 -progressUseColor=0"
        """
        for key in keys:
            self.param(key, false_value)
        return self

    def add_rez_package(self, package: str):
        """
        Add one rez package that will be added to the final command

        Examples:
            CommandBuilder("maya", rez_packages=["maya", "python3"]) -> "rez env maya python3 -- maya"
        """
        self.rez_packages.append(package)

    def as_argv(self) -> List[str]:
        """
        Return the full command as a list of string tokens

        Examples:
            CommandBuilder("du", dashes="-", delimiter=" ").param("d", 1).param("h") -> ["du", "-d", "1", "-h"]
        """

        args: List[str] = []

        for (key, value) in self.params:
            if key:
                param = f"{self.dashes}{key}"

                if value is not None:
                    # If we have a delimiter like key=value
                    if self.delimiter is not None and self.delimiter != " ":
                        param += f"{self.delimiter}{str(value)}"
                        args.append(param)
                    else:
                        # If there's no delimiter it can be a single value or a list of values
                        # Eg: -key value / -key v1 v2 v3
                        args.append(param)
                        values = value if type(value) == list else [value]
                        args.extend(map(str, values))
                else:
                    # If there's no value we append the key alone
                    # Eg: ls -l
                    args.append(str(param))
            else:
                if value is not None:
                    # Add a single value without key
                    args.append(str(value))

        command = ([self.executable] + args) if self.executable else args

        # Add rez packages to the command
        if self.rez_packages:
            command = ["rez", "env"] + self.rez_packages + ["--"] + command

        return command

    def deepcopy(self):
        """
        Returns a deep copy of the command
        Useful when creating new commands
        """
        return copy.deepcopy(self)

    def __repr__(self) -> str:
        return " ".join(self.as_argv())
