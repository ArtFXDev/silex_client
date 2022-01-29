"""
@author: TD gang

Unit testing functions for the class ActionQuery
"""

import pytest

from silex_client.action.action_query import ActionQuery
from silex_client.core.context import Context
from silex_client.resolve.config import Config
from silex_client.utils.enums import Status

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

    future = action.execute(batch=True)

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED


def test_execute_tester_action(dummy_context: Context):
    """
    Test the execution of all the commands in the 'testing' action
    """
    action = ActionQuery("tester", category="dev")
    assert hasattr(action, "buffer")

    future = action.execute(batch=True)

    # Let the execution of the action happen in the event loop thread
    future.result()

    assert action.status is Status.COMPLETED
