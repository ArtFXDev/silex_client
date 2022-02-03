from __future__ import annotations

import asyncio
import logging
import typing
from typing import Any, Dict

from fileseq import FrameSet


from silex_client.utils.enums import Status
from silex_client.action.command_base import CommandBase
from silex_client.utils.parameter_types import (
    IntArrayParameterMeta,
    MultipleSelectParameterMeta,
    PathParameterMeta,
    RadioSelectParameterMeta,
    RangeParameterMeta,
    SelectParameterMeta,
    TaskParameterMeta,
    TextParameterMeta,
)

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
            "value": "John Doe",
            "tooltip": "Testing the string parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return {"testing_values": parameters["string_tester"]}


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
            "value": 39,
            "tooltip": "Testing the int parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
            "value": False,
            "tooltip": "Testing the bool parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["bool_tester"]

    async def setup(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        if not parameters["bool_tester"]:
            self.command_buffer.parameters["bool_tester_2"].hide = True
        else:
            self.command_buffer.parameters["bool_tester_2"].hide = False


class PathTester(CommandBase):
    """
    Testing the path parameters
    """

    parameters = {
        "path_tester": {
            "label": "Path Tester",
            "type": PathParameterMeta(),
            "value": None,
            "tooltip": "Testing the path parameters",
        },
        "path_tester_multiple": {
            "label": "Path Tester Multiple",
            "type": PathParameterMeta(multiple=True),
            "value": None,
        },
        "path_tester_extensions": {
            "label": "Path Tester extensions .abc, .obj, .fbx",
            "type": PathParameterMeta(extensions=[".abc", ".obj", ".fbx"]),
            "value": None,
        },
        "path_tester_multiple_extensions": {
            "label": "Path Tester multiple files and extensions (.png, .jpg, .jpeg)",
            "type": PathParameterMeta(
                extensions=[".png", ".jpg", ".jpeg"], multiple=True
            ),
            "value": None,
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
            "type": SelectParameterMeta(
                **{
                    "Hello Label": "hello",
                    "World Label": "world",
                    "Foo Label": "foo",
                    "Bar Label": "bar",
                }
            ),
            "value": None,
            "tooltip": "Testing the select parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        self,
        parameters: Dict[str, Any],
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
            "value": 5000,
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["range_tester"]


class EntityTester(CommandBase):
    """
    Testing the entity parameters
    """

    parameters = {
        "entity_tester": {
            "label": "Entity Tester",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Testing the entity parameters",
        },
        "entity_tester_2": {
            "label": "Entity Tester 2",
            "type": TaskParameterMeta(),
            "value": None,
            "tooltip": "Testing the entity parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        logger.info(
            "Entity parameter tester: %s, %s",
            parameters["entity_tester"],
            type(parameters["entity_tester"]),
        )
        logger.info(
            "Entity parameter tester: %s, %s",
            parameters["entity_tester_2"],
            type(parameters["entity_tester_2"]),
        )
        return parameters["entity_tester"]


class MultipleSelectTester(CommandBase):
    """
    Testing the multiple_select parameters
    """

    parameters = {
        "multiple_select_tester": {
            "label": "MultipleSelect Tester",
            "type": MultipleSelectParameterMeta("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the multiple_select parameters",
        },
        "multiple_select_tester_2": {
            "label": "MultipleSelect Tester 2",
            "type": MultipleSelectParameterMeta("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the multiple_select parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["multiple_select_tester"]


class RadioSelectTester(CommandBase):
    """
    Testing the radio_select parameters
    """

    parameters = {
        "radio_select_tester": {
            "label": "RadioSelect Tester",
            "type": RadioSelectParameterMeta("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the radio_select parameters",
        },
        "radio_select_tester_2": {
            "label": "RadioSelect Tester 2",
            "type": RadioSelectParameterMeta("foo", "bar", "hello", "world"),
            "value": None,
            "tooltip": "Testing the radio_select parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["radio_select_tester"]


class IntArrayTesterLow(CommandBase):
    """
    Testing the int_array parameters
    """

    parameters = {
        "int_array_tester": {
            "label": "IntArray Tester",
            "type": IntArrayParameterMeta(2),
            "value": None,
            "tooltip": "Testing the int_array parameters",
        },
        "int_array_tester_2": {
            "label": "IntArray Tester 2",
            "type": IntArrayParameterMeta(2),
            "value": None,
            "tooltip": "Testing the int_array parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["int_array_tester"]


class IntArrayTesterHigh(CommandBase):
    """
    Testing the int_array parameters
    """

    parameters = {
        "int_array_tester": {
            "label": "IntArray Tester",
            "type": IntArrayParameterMeta(6),
            "value": None,
            "tooltip": "Testing the int_array parameters",
        },
        "int_array_tester_2": {
            "label": "IntArray Tester 2",
            "type": IntArrayParameterMeta(6),
            "value": None,
            "tooltip": "Testing the int_array parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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

        return parameters["int_array_tester"]


class ProgressTester(CommandBase):
    """
    Testing the progress on info parameters
    """

    parameters = {
        "progress_tester": {
            "label": "Progress Tester",
            "type": TextParameterMeta(color="info", progress={"variant": "indeterminate"}),
            "value": "This command will take time to execute and show its progress",
            "tooltip": "Testing the range parameters",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
        action_query: ActionQuery,
        logger: logging.Logger,
    ):
        progress_parameter = self.command_buffer.parameters["progress_tester"]
        self.command_buffer.status = Status.WAITING_FOR_RESPONSE

        progress_parameter.rebuild_type(color="info", progress={"variant": "determinate", "value": 0})
        action_query.update_websocket()
        await asyncio.sleep(1)
        logger.info("Pretending to work")
        progress_parameter.rebuild_type(color="info", progress={"variant": "determinate", "value": 33})
        progress_parameter.value = "Pretending to work"
        action_query.update_websocket()
        await asyncio.sleep(1)
        logger.info("Keep pretending to work")
        progress_parameter.rebuild_type(color="info", progress={"variant": "determinate", "value": 66})
        progress_parameter.value = "Keep pretending to work"
        action_query.update_websocket()
        logger.info("Work done")
        await asyncio.sleep(1)
        progress_parameter.rebuild_type(color="info", progress={"variant": "determinate", "value": 100})
        progress_parameter.value = "Work done"
        action_query.update_websocket()
        await asyncio.sleep(1)


class TextTester(CommandBase):
    """
    Testing the text parameters
    """

    parameters = {
        "text_tester": {
            "label": "Text Tester",
            "type": TextParameterMeta(),
            "value": None,
            "tooltip": "Testing the text parameters",
        },
        "text_tester_2": {
            "label": "Text Tester 2",
            "type": TextParameterMeta(),
            "value": "Lorem ipsum dolor sit amet",
            "tooltip": "Testing the text parameters",
        },
        "text_tester_with_returns": {
            "label": "Text Tester with returns",
            "type": TextParameterMeta(),
            "value": "First line\nSecond line\nThird line\n\nEnd",
        },
        "text_tester_info": {
            "label": "Text Tester Info",
            "type": TextParameterMeta(color="info"),
            "value": "You are doing well! ℹ️",
        },
        "text_tester_success": {
            "label": "Text Tester Success",
            "type": TextParameterMeta(color="success"),
            "value": "You are doing well! ✅",
        },
        "text_tester_warning": {
            "label": "Text Tester Warning",
            "type": TextParameterMeta(color="warning"),
            "value": "Be careful... ⚠️",
        },
        "text_tester_error": {
            "label": "Text Tester Error",
            "type": TextParameterMeta(color="error"),
            "value": "Something went wrong! 🚫",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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

        return parameters["text_tester"]


class FrameSetTester(CommandBase):
    """
    Testing the frame set parameters
    """

    parameters = {
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

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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

        return parameters["frameset_tester"]


class TracebackTester(CommandBase):
    """
    Testing the int_array parameters
    """

    parameters = {
        "raise_exception": {
            "label": "Raise exception",
            "type": bool,
            "value": True,
            "tooltip": "Specify if you what this command to rase an exception or not",
        },
    }

    @CommandBase.conform_command()
    async def __call__(
        self,
        parameters: Dict[str, Any],
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
        return parameters["raise_exception"]
