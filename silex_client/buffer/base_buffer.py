from __future__ import annotations

from abc import ABC
import re
import uuid as unique_id
from dataclasses import dataclass, field
import textwrap
from typing import Optional

from silex_client.utils.files import slugify


@dataclass()
class BaseBuffer(ABC):
    """
    A buffer can be serialized and deserialized to json format. It is used
    as a communication payload between the different parts of silex. Each part
    can update the buffer.

    Example:

                      [buffer]                    [buffer]
        silex-client <---------> socket-service <----------> silex-front
    """

    #: Name of the buffer, must have no space or special characters
    name: str = field()

    #: The name of the buffer, only meant to be displayed in the interface
    label: Optional[str] = field(compare=False, repr=False, default=None)

    #: Parent in the buffer hierarchy
    parent: Optional[BaseBuffer] = field(compare=False, repr=False, default=None)

    #: Specify if the buffer must be displayed by the UI or not, hidden buffer are not sent at all
    hide: bool = field(compare=False, repr=False, default=False)

    #: Small explanation for the user
    tooltip: Optional[str] = field(compare=False, repr=False, default=None)

    #: A Unique ID to help differentiate multiple buffers
    uuid: str = field(default_factory=lambda: str(unique_id.uuid4()))

    #: Marquer to know if the serialize cache is outdated or not
    outdated_cache: bool = field(compare=False, repr=False, default=True)

    #: Cache of the serialize output, only for performance improvment
    serialize_cache: dict = field(compare=False, repr=False, default_factory=dict)

    def __setattr__(self, name, value):
        """
        Everytime an attribute of this buffer is set, this will help setting the
        outdated_cache attribute for you automatically, so you don't have to set
        outdated_cache = True every time you modify an attribute of the buffer

        Warning: This does not work when modifying container attributes, appending
        a value to a list attribute does not call __setattr__
        """

        super().__setattr__("outdated_cache", True)
        super().__setattr__(name, value)

    def __post_init__(self):
        if self.label is None:
            # The label can be guessed from the name, by making it prettier
            deslugify_pattern = re.compile("[^A-Za-z0-9]")
            self.label = deslugify_pattern.sub(" ", self.name)
            self.label = self.label.title()

        # Allow tooltip to be written with multiline strings
        if self.tooltip is not None:
            self.tooltip = textwrap.dedent(self.tooltip)

        # The name must not have any space/special characters
        self.name = slugify(self.name)
