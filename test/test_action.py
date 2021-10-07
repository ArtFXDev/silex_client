"""
@author: TD gang

Unit testing functions for the module core.context
"""

import os
import pytest
from concurrent import futures

from silex_client.core.context import Context
from silex_client.utils.enums import Status
from silex_client.resolve.loader import Loader


@pytest.fixture
def dummy_context() -> Context:
    """
    Return a context initialized in the test folder to work the configuration files
    that has been created only for test purpose
    """
    context = Context.get()
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    context.config.action_search_path.insert(0, config_root)
    context.update_metadata({"project": "TEST_PIPE"})
    context.is_outdated = False
    return context


def test_get_action(dummy_context: Context):
    """
    Test if the resolved action by the context is the same as if we try to resolve it manually
    """
    resolved_action = dummy_context.get_action("publish")

    # Load the file manualy and check if it correspond to the resolved file
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    action_file = os.path.join(config_root, "publish.yml")
    # Compare the two config
    with open(action_file, "r") as config_data:
        loader = Loader(config_data, tuple(config_root))
        manual_action = loader.get_single_data()["publish"]["steps"]
        assert len(resolved_action.buffer.steps["pre_action"].commands.values()) == len(
            manual_action["pre_action"]["commands"].values()
        )
        assert len(resolved_action.buffer.steps["action"].commands.values()) == len(
            manual_action["action"]["commands"].values()
        )
        assert len(
            resolved_action.buffer.steps["post_action"].commands.values()
        ) == len(manual_action["post_action"]["commands"].values())
        loader.dispose()


def test_execute_action(dummy_context: Context):
    """
    Test the execution of all the commands in the 'foo' action from the config
    given by the dummy_context
    """
    action = dummy_context.get_action("publish")
    # Add some fake value to mimic the UI editing the parameters
    action.buffer.set_parameter("action", "publish_file", "file_path", "/path/to/file")

    dummy_context.event_loop.start()
    future = action.execute()
    # Let the execution of the action happen in the event loop thread
    futures.wait([future])
    dummy_context.event_loop.stop()
    for command in action.commands:
        print(command.status)
    assert action.status is Status.COMPLETED
