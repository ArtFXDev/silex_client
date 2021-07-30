from __future__ import annotations
import importlib
import re
import uuid
import typing
from dataclasses import dataclass, field

from silex_client.utils.log import logger

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.command_base import CommandBase


@dataclass()
class CommandBuffer():
    """
    Store the data of a command
    """
    uid: uuid.UUID = field(default_factory=uuid.uuid1)
    name: str = field(default="untitled")
    label: str = field(compare=False, repr=False, default="Untitled")
    executor: CommandBase = field(compare=False, init=False, repr=False)
    parameters: list = field(compare=False, repr=False, default_factory=list)
    variables: dict = field(repr=False, compare=False, default_factory=dict)
    valid: bool = field(repr=False, default=True)
    return_code: int = field(default=0)

    def __init__(self,
                 path: str,
                 name: str = None,
                 label: str = None,
                 **kwargs):
        # Get the command object
        try:
            split_path = path.split(".")
            module = importlib.import_module(".".join(split_path[:-1]))
            executor = getattr(module, split_path[-1])
            if module is CommandBase:
                self.executor = executor
            else:
                raise ImportError
        except (ImportError, AttributeError):
            logger.error("Invalid command path, skipping %s", path)
            self.valid = False

        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command name
        if name is None:
            name = slugify_pattern.sub("_", path)
        self.name = name
        # Set the command label
        if label is None:
            label = slugify_pattern.sub(" ", name)
            label = label.title()
        self.label = label
        # Set the extra attributes
        self.extra_attributes = kwargs

    def __call__(self, **extra_variables):
        executor = self.executor(self)
        executor(**extra_variables)
