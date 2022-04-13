from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from silex_client.graph.step import Step



@dataclass()
class Action(Step):
    """
    An action is always at the root of an action tree.
    """

    #: Snapshot of the context's metadata when the action is created
    context_metadata: Dict[str, Any] = field(default_factory=dict)

    #: The thumbnail is only for user display
    thumbnail: Optional[str] = field(default=None)

    #: Category when displaying the action in shelves of DCCs
    shelf: Optional[str] = field(default=None)

    #: This attribute follows the composite design pattern
    children: Dict[str, Step] = field(default_factory=dict)
