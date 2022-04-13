from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from silex_client.graph.graph_item import GraphItem
from silex_client.graph.pluggable_item import PluggableItem
from silex_client.utils.enums import Status


@dataclass()
class Command(GraphItem, PluggableItem):
    """
    A command can be executed, it stores the data of the resolved definition.
    """

    #: The name of the command definition
    definition: Optional[str] = field(default=None)

    #: The index defines the order in wich the commands are iterated
    index: int = field(default=0)

    #: Specify if the command should be prompting the user before execution
    prompt: bool = field(compare=False, repr=False, default=False)

    #: The status has an impact on the UI but will also stop the execution in case of error
    status: Status = field(default=Status.INITIALIZED, init=False)

    #: List of all the logs during the execution of that command
    logs: List[Dict[str, str]] = field(default_factory=list)

    #: Defines if the command must be executed or not
    skip: bool = field(default=False)

    #: The progress is only for the UI, it should go from 0 to 100
    progress: Optional[int] = field(default=None)
