from __future__ import annotations

import logging
import os
import typing
from typing import Any, Dict, List, cast

from silex_client.action.command_base import CommandBase
from silex_client.utils import farm
from silex_client.utils.parameter_types import (
    ListParameterMeta,
    MultipleSelectParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
)

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery



class SubmitToDeadlineCommand(CommandBase):
  pass