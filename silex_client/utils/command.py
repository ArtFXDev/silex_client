from typing import Any, Dict, List, Optional


class CommandBuilder:
    """
    Used to construct a command with arguments with the format: executable {-key=value}
    """

    def __init__(self, executable: str):
        self.executable = executable
        self.rez_cmd = None
        self.params: Dict[str, Optional[str]] = {}

    def param(self, key: str, value: Any = None):
        """
        Add a parameter to the command
        """
        self.params[key] = value
        return self
    
    def disable(self, keys: List[str], false_value=0):
        """
        Set multiple keys with a false value
        """
        for key in keys:
            self.param(key, false_value)
        return self

    def add_rez_env(self, packages: List[str]):
        """
        Set the rez packages that will be resolved with this command
        """
        self.rez_cmd = ["rez", "env"] + packages + ["--"]

    def as_argv(self) -> List[str]:
        """
        Return the full command as a list of tokens (argv)
        """
        args = [
            f"-{key}={value}" if value is not None else f"-{key}"
            for (key, value) in self.params.items()
        ]
        command: List[str] = [self.executable] + args

        if self.rez_cmd:
            print(self.rez_cmd)
            print(command)
            command = self.rez_cmd + command

        return command

    def __repr__(self) -> str:
        return " ".join(self.as_argv())
