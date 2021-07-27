import importlib
import re
from dataclasses import dataclass, field

from silex_client.utils.log import logger


@dataclass()
class CommandBuffer():
    """
    Store the data of a command
    """
    path: str = field()
    name: str = field(default="untitled")
    label: str = field(compare=False, repr=False, default="Untitled")
    executor: object = field(compare=False, default_factory=object, repr=False)
    parameters: list = field(compare=False, repr=False, default_factory=list)
    valid: bool = field(repr=False, default=True)
    overridable: bool = field(repr=False, default=True)
    extra_attributes: dict = field(repr=False, default_factory=dict)

    def __init__(self,
                 path: str,
                 name: str = None,
                 label: str = None,
                 **kwargs):
        # Get the command object
        self.path = path
        try:
            self.executor = importlib.import_module(path)
        except ImportError:
            logger.error("Invalid command path, skipping %s" % path)
            self.valid = False

        slugify_pattern = re.compile("[^A-Za-z0-9]")
        # Set the command name
        if name is None:
            name = slugify_pattern.sub("_", path)
            self.overridable = False
        self.name = name
        # Set the command label
        if label is None:
            label = slugify_pattern.sub(" ", name)
            label = label.title()
        self.label = label
        # Set the extra attributes
        self.extra_attributes = kwargs

    def __call__(self, **extra_variables):
        # TODO: Implement the call the given command
        pass
