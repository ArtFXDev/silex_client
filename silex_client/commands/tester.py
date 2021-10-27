from __future__ import annotations

import os
import typing
import pathlib
from typing import Any, Dict

from silex_client.action.command_base import CommandBase
from silex_client.utils.log import logger
from silex_client.utils.parameter_types import RangeParameterMeta, SelectParameterMeta

# Forward references
if typing.TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class StringTester(CommandBase):
    """
    Testing the string parameters
    """

    parameters = {
        "string_tester": {
            "label": "String Tester",
            "type": str,
            "value": None,
            "tooltip": "Testing the string parameters",
        },
        "string_tester_2": {
            "label": "String Tester 2",
            "type": str,
            "value": None,
            "tooltip": "Testing the string parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "String parameter tester: %s, %s",
            parameters["string_tester"],
            type(parameters["string_tester"]),
        )
        logger.info(
            "String parameter tester 2: %s, %s",
            parameters["string_tester_2"],
            type(parameters["string_tester_2"]),
        )
        return parameters["string_tester"]


class IntegerTester(CommandBase):
    """
    Testing the int parameters
    """

    parameters = {
        "int_tester": {
            "label": "Integer Tester",
            "type": int,
            "value": None,
            "tooltip": "Testing the int parameters",
        },
        "int_tester_2": {
            "label": "Integer Tester 2",
            "type": int,
            "value": None,
            "tooltip": "Testing the int parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Integer parameter tester: %s, %s",
            parameters["int_tester"],
            type(parameters["int_tester"]),
        )
        logger.info(
            "Integer parameter tester_2: %s, %s",
            parameters["int_tester_2"],
            type(parameters["int_tester_2"]),
        )
        return parameters["int_tester"]


class BooleanTester(CommandBase):
    """
    Testing the bool parameters
    """

    parameters = {
        "bool_tester": {
            "label": "Boolean Tester",
            "type": bool,
            "value": None,
            "tooltip": "Testing the bool parameters",
        },
        "bool_tester_2": {
            "label": "Boolean Tester 2",
            "type": bool,
            "value": None,
            "tooltip": "Testing the bool parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Boolean parameter tester: %s, %s",
            parameters["bool_tester"],
            type(parameters["bool_tester"]),
        )
        logger.info(
            "Boolean parameter tester_2: %s, %s",
            parameters["bool_tester_2"],
            type(parameters["bool_tester_2"]),
        )
        return parameters["bool_tester"]


class PathTester(CommandBase):
    """
    Testing the path parameters
    """

    parameters = {
        "path_tester": {
            "label": "Path Tester",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Testing the path parameters",
        },
        "path_tester_2": {
            "label": "Path Tester 2",
            "type": pathlib.Path,
            "value": None,
            "tooltip": "Testing the path parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Path parameter tester: %s, %s",
            parameters["path_tester"],
            type(parameters["path_tester"]),
        )
        logger.info(
            "Path parameter tester: %s, %s",
            parameters["path_tester_2"],
            type(parameters["path_tester_2"]),
        )
        return parameters["path_tester"]


class SelectTester(CommandBase):
    """
    Testing the select parameters
    """

    parameters = {
        "select_tester": {
            "label": "Select Tester",
            "type": SelectParameterMeta("hello", "world", "foo", "bar"),
            "value": None,
            "tooltip": "Testing the select parameters",
        },
        "select_tester_2": {
            "label": "Select Tester 2",
            "type": SelectParameterMeta("hello", "world", "foo", "bar"),
            "value": None,
            "tooltip": "Testing the select parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Select parameter tester: %s, %s",
            parameters["select_tester"],
            type(parameters["select_tester"]),
        )
        logger.info(
            "Select parameter tester: %s, %s",
            parameters["select_tester_2"],
            type(parameters["select_tester_2"]),
        )
        return parameters["select_tester"]


class RangeTesterLow(CommandBase):
    """
    Testing the range parameters
    """

    parameters = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeParameterMeta(1, 475, 1),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeParameterMeta(1, 475, 1),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester"],
            type(parameters["range_tester"]),
        )
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester_2"],
            type(parameters["range_tester_2"]),
        )
        return parameters["range_tester"]


class RangeTesterMid(CommandBase):
    """
    Testing the range parameters
    """

    parameters = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeParameterMeta(1, 30, 5),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeParameterMeta(1, 30, 5),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester"],
            type(parameters["range_tester"]),
        )
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester_2"],
            type(parameters["range_tester_2"]),
        )
        return parameters["range_tester"]


class RangeTesterHigh(CommandBase):
    """
    Testing the range parameters
    """

    parameters = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeParameterMeta(1000, 10000, 100),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeParameterMeta(1000, 10000, 100),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self, upstream: Any, parameters: Dict[str, Any], action_query: ActionQuery
    ):
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester"],
            type(parameters["range_tester"]),
        )
        logger.info(
            "Range parameter tester: %s, %s",
            parameters["range_tester_2"],
            type(parameters["range_tester_2"]),
        )
        return parameters["range_tester"]
