from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from silex_client.graph.socket import Socket


@dataclass()
class PluggableItem:
    """
    Some graph item can be connected together via inputs and outputs,
    like the commands and the steps.
    This mixin implement the nessesary fields to have inputs and outputs.

    Example:

         |-----------|        |-----------|
        o| pluggable |o ---- o| pluggable |o
         |-----------|        |-----------|
    """

    #: Name of the item, must have no space or special characters
    inputs: Dict[str, Socket] = field(default_factory=dict)

    #: The name of the item, only meant to be displayed in the interface
    outputs: Dict[str, Socket] = field(default_factory=dict)
