"""
@author: TD gang

Unit testing functions for the module core.context
"""

import pytest
import os
import pathlib
import shutil
from pytest_mock import MockFixture, MockerFixture
from concurrent import futures
from unittest.mock import Mock

from silex_client.core.context import Context
from silex_client.action.action_query import ActionQuery
from silex_client.utils.enums import Status
from silex_client.resolve.config import Config

from .test_config import dummy_config


@pytest.fixture
def dummy_context() -> Context:
    """
    Return a context initialized in the test folder to work the configuration files
    that has been created only for test purpose
    """
    context = Context.get()
    context.update_metadata({"project": "TEST_PIPE"})
    context.is_outdated = False
    if not context.event_loop.is_running:
        context.start_services()
    return context


def test_execute_foo_action(dummy_config: Config, dummy_context: Context):
    """
    Test the execution of all the commands in the 'foo' action
    """
    action = ActionQuery("foo", category="test")
    assert hasattr(action, "buffer")

    future = action.execute()

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED


def test_execute_tester_action(dummy_context: Context):
    """
    Test the execution of all the commands in the 'testing' action
    """
    action = ActionQuery("tester", category="dev")
    assert hasattr(action, "buffer")

    # Set the parameter that are required for the execution
    action.set_parameter("parameter_tester:path:path_tester", "/foo/bar")
    action.set_parameter("parameter_tester:path:path_tester_multiple", "/foo/bar")
    action.set_parameter("parameter_tester:path:path_tester_extensions", "/foo/bar")
    action.set_parameter("parameter_tester:path:path_tester_multiple_extensions", "/foo/bar")
    future = action.execute()

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED

def test_execute_conform_action(mocker: MockFixture, dummy_context: Context):
    """
    Test the execution of all the commands in the 'conform' action
    """
    action = ActionQuery("conform")
    assert hasattr(action, "buffer")

    mock = mocker.MagicMock()
    mock.__getitem__.side_effect = lambda x: getattr(mock, x)

    output_path = pathlib.Path(__file__).parent / "tmp" / "conform"
    input_path = pathlib.Path(__file__).parent / "tmp" / "unittest_conform.obj"
    final_path = pathlib.Path(__file__).parent / "tmp" / "unittest_conform" / "conform_unittest_conform.obj"

    # Patch the gazu functions
    mocker.patch(
        'silex_client.commands.build_output_path.gazu.task.get_task',
        return_value=mock
    )
    mocker.patch(
        'silex_client.commands.build_output_path.gazu.files.get_output_type_by_short_name',
        return_value=mock
    )
    mocker.patch(
        'silex_client.commands.build_output_path.gazu.files.build_entity_output_file_path',
        return_value=output_path
    )

    # Set the parameter that are required for the execution
    os.makedirs(input_path.parent)
    input_path.touch()
    action.set_parameter("setup:get_conform_output:file_paths", input_path)
    future = action.execute()

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED
    assert final_path.exists()
    shutil.rmtree(pathlib.Path(__file__).parent / "tmp")
