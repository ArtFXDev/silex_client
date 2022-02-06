"""
@author: TD gang
@github: https://github.com/ArtFXDev

Definition of multiple commands that are for testing purpose only
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from fileseq import FrameSet

from silex_client.action.command_definition import CommandDefinition
from silex_client.action.command_sockets import CommandSockets
from silex_client.utils.socket_types import (
    IntArrayType,
    MultipleSelectType,
    PathType,
    RadioSelectType,
    RangeType,
    SelectType,
    TaskType,
    TextType,
)

# Forward references
if TYPE_CHECKING:
    from silex_client.action.action_query import ActionQuery


class StringTester(CommandDefinition):
    """
    Testing the string parameters
    """

    inputs = {
        "string_tester": {
            "label": "String Tester",
            "type": str,
            "value": None,
            "tooltip": "Testing the string parameters",
        },
        "string_tester_2": {
            "label": "String Tester 2",
            "type": str,
            "value": "John Doe",
            "tooltip": "Testing the string parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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


class IntegerTester(CommandDefinition):
    """
    Testing the int parameters
    """

    inputs = {
        "int_tester": {
            "label": "Integer Tester",
            "type": int,
            "value": None,
            "tooltip": "Testing the int parameters",
        },
        "int_tester_2": {
            "label": "Integer Tester 2",
            "type": int,
            "value": 39,
            "tooltip": "Testing the int parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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


class BooleanTester(CommandDefinition):
    """
    Testing the bool parameters
    """

    inputs = {
        "bool_tester": {
            "label": "Boolean Tester",
            "type": bool,
            "value": None,
            "tooltip": "Testing the bool parameters",
        },
        "bool_tester_2": {
            "label": "Boolean Tester 2",
            "type": bool,
            "value": False,
            "tooltip": "Testing the bool parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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

    async def setup(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        parameters.get_buffer("bool_tester_2").hide = not parameters["bool_tester"]


class PathTester(CommandDefinition):
    """
    Testing the path parameters
    """

    inputs = {
        "path_tester": {
            "label": "Path Tester",
            "type": PathType(),
            "value": None,
            "tooltip": "Testing the path parameters",
        },
        "path_tester_multiple": {
            "label": "Path Tester Multiple",
            "type": PathType(multiple=True),
            "value": None,
        },
        "path_tester_extensions": {
            "label": "Path Tester extensions .abc, .obj, .fbx",
            "type": PathType(extensions=[".abc", ".obj", ".fbx"]),
            "value": None,
        },
        "path_tester_multiple_extensions": {
            "label": "Path Tester multiple files and extensions (.png, .jpg, .jpeg)",
            "type": PathType(extensions=[".png", ".jpg", ".jpeg"], multiple=True),
            "value": None,
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Path parameter tester: %s, %s",
            parameters["path_tester"],
            type(parameters["path_tester"]),
        )
        logger.info(
            "Path parameter multiple: %s, %s",
            parameters["path_tester_multiple"],
            type(parameters["path_tester_multiple"]),
        )
        logger.info(
            "Path parameter extensions: %s, %s",
            parameters["path_tester_extensions"],
            type(parameters["path_tester_extensions"]),
        )
        logger.info(
            "Path parameter multiple extensions: %s, %s",
            parameters["path_tester_multiple_extensions"],
            type(parameters["path_tester_multiple_extensions"]),
        )


class SelectTester(CommandDefinition):
    """
    Testing the select parameters
    """

    inputs = {
        "select_tester": {
            "label": "Select Tester",
            "type": SelectType("hello", "world", "foo", "bar"),
            "value": None,
            "tooltip": "Testing the select parameters",
        },
        "select_tester_2": {
            "label": "Select Tester 2",
            "type": SelectType(
                **{
                    "Hello Label": "hello",
                    "World Label": "world",
                    "Foo Label": "foo",
                    "Bar Label": "bar",
                }
            ),
            "value": "bar",
            "tooltip": "Testing the select parameters",
        },
    }

    outputs = {
        "test_return_select": {
            "label": "Select Return",
            "type": SelectType("hello", "world", "foo", "bar"),
            "value": None,
            "tooltip": "Testing the return of select type",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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
        return {"test_return_select": parameters["select_tester"]}


class RangeTesterLow(CommandDefinition):
    """
    Testing the range parameters
    """

    inputs = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeType(1, 475, 1),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeType(1, 475, 1),
            "value": 300,
            "tooltip": "Testing the range parameters",
        },
    }

    outputs = {
        "test_return_range": {
            "label": "Range Return",
            "type": RangeType(1, 475, 1),
            "value": None,
            "tooltip": "Testing the return of a range type",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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
        return {"test_return_range": parameters["range_tester"]}


class RangeTesterMid(CommandDefinition):
    """
    Testing the range parameters
    """

    inputs = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeType(1, 30, 5),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeType(1, 30, 5),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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

        await asyncio.sleep(1)
        logger.info("Pretending to work")
        await asyncio.sleep(1)
        logger.info("Keep pretending to work")
        await asyncio.sleep(1)
        logger.info("Work done")
        await asyncio.sleep(1)


class RangeTesterHigh(CommandDefinition):
    """
    Testing the range parameters
    """

    inputs = {
        "range_tester": {
            "label": "Range Tester",
            "type": RangeType(1000, 10000, 100),
            "value": None,
            "tooltip": "Testing the range parameters",
        },
        "range_tester_2": {
            "label": "Range Tester 2",
            "type": RangeType(1000, 10000, 100),
            "value": 5500,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
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


class TaskTester(CommandDefinition):
    """
    Testing the task parameters
    """

    inputs = {
        "task_tester": {
            "label": "Task Tester",
            "type": TaskType(),
            "value": None,
            "tooltip": "Testing the task parameters",
        },
        "task_tester_2": {
            "label": "Task Tester 2",
            "type": TaskType(),
            "value": None,
            "tooltip": "Testing the task parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Task parameter tester: %s, %s",
            parameters["task_tester"],
            type(parameters["task_tester"]),
        )
        logger.info(
            "Task parameter tester: %s, %s",
            parameters["task_tester_2"],
            type(parameters["task_tester_2"]),
        )


class MultipleSelectTester(CommandDefinition):
    """
    Testing the multiple_select parameters
    """

    inputs = {
        "multiple_select_tester": {
            "label": "MultipleSelect Tester",
            "type": MultipleSelectType("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the multiple_select parameters",
        },
        "multiple_select_tester_2": {
            "label": "MultipleSelect Tester 2",
            "type": MultipleSelectType("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the multiple_select parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "MultipleSelect parameter tester: %s, %s",
            parameters["multiple_select_tester"],
            type(parameters["multiple_select_tester"]),
        )
        logger.info(
            "MultipleSelect parameter tester: %s, %s",
            parameters["multiple_select_tester_2"],
            type(parameters["multiple_select_tester_2"]),
        )


class RadioSelectTester(CommandDefinition):
    """
    Testing the radio_select parameters
    """

    inputs = {
        "radio_select_tester": {
            "label": "RadioSelect Tester",
            "type": RadioSelectType("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the radio_select parameters",
        },
        "radio_select_tester_2": {
            "label": "RadioSelect Tester 2",
            "type": RadioSelectType("foo", "bar", "hello", "world"),
            "value": "world",
            "tooltip": "Testing the radio_select parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Select Radio parameter tester: %s, %s",
            parameters["radio_select_tester"],
            type(parameters["radio_select_tester"]),
        )
        logger.info(
            "Select Radio parameter tester: %s, %s",
            parameters["radio_select_tester_2"],
            type(parameters["radio_select_tester_2"]),
        )


class IntArrayTester(CommandDefinition):
    """
    Testing the int_array parameters
    """

    inputs = {
        "int_array_tester": {
            "label": "IntArray Tester",
            "type": IntArrayType(2),
            "value": None,
            "tooltip": "Testing the int_array parameters",
        },
        "int_array_tester_2": {
            "label": "IntArray Tester 2",
            "type": IntArrayType(6),
            "value": [3, 4, 2, 39, 204, 3],
            "tooltip": "Testing the int_array parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "IntArray parameter tester: %s, %s",
            parameters["int_array_tester"],
            type(parameters["int_array_tester"]),
        )
        logger.info(
            "IntArray parameter tester: %s, %s",
            parameters["int_array_tester_2"],
            type(parameters["int_array_tester_2"]),
        )


class TextTester(CommandDefinition):
    """
    Testing the text parameters
    """

    inputs = {
        "text_tester": {
            "label": "Text Tester",
            "type": TextType(),
            "value": None,
            "tooltip": "Testing the text parameters",
        },
        "text_tester_2": {
            "label": "Text Tester 2",
            "type": TextType(),
            "value": "Lorem ipsum dolor sit amet",
            "tooltip": "Testing the text parameters",
        },
        "text_tester_with_returns": {
            "label": "Text Tester with returns",
            "type": TextType(),
            "value": "First line\nSecond line\nThird line\n\nEnd",
        },
        "text_tester_info": {
            "label": "Text Tester Info",
            "type": TextType(color="info"),
            "value": "You are doing well! ℹ️",
        },
        "text_tester_success": {
            "label": "Text Tester Success",
            "type": TextType(color="success"),
            "value": "You are doing well! ✅",
        },
        "text_tester_warning": {
            "label": "Text Tester Warning",
            "type": TextType(color="warning"),
            "value": "Be careful... ⚠️",
        },
        "text_tester_error": {
            "label": "Text Tester Error",
            "type": TextType(color="error"),
            "value": "Something went wrong! 🚫",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Text parameter tester: %s, %s",
            parameters["text_tester"],
            type(parameters["text_tester"]),
        )
        logger.info(
            "Text parameter tester: %s, %s",
            parameters["text_tester_2"],
            type(parameters["text_tester_2"]),
        )


class FrameSetTester(CommandDefinition):
    """
    Testing the frame set parameters
    """

    inputs = {
        "frameset_tester": {
            "label": "FrameSet Tester",
            "type": FrameSet,
            "value": None,
            "tooltip": "Testing the frameset parameters",
        },
        "frameset_tester_2": {
            "label": "FrameSet Tester 2",
            "type": FrameSet,
            "value": "1-50x5",
            "tooltip": "Testing the frameset parameters",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "FramseSet parameter tester: %s, %s",
            parameters["frameset_tester"],
            type(parameters["frameset_tester"]),
        )
        logger.info(
            "FramseSet parameter tester: %s, %s",
            parameters["frameset_tester_2"],
            type(parameters["frameset_tester_2"]),
        )


class TracebackTester(CommandDefinition):
    """
    Testing the int_array parameters
    """

    inputs = {
        "raise_exception": {
            "label": "Raise exception",
            "type": bool,
            "value": True,
            "tooltip": "Specify if you what this command to rase an exception or not",
        },
    }

    @CommandDefinition.validate()
    async def __call__(
        self,
        parameters: CommandSockets,
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Traceback tester: %s, %s",
            parameters["raise_exception"],
            type(parameters["raise_exception"]),
        )

        if parameters["raise_exception"]:
            raise ValueError("Don't worry, this is a fake error for testing purpose")
