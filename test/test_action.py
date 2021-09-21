"""
@author: TD gang

Unit testing functions for the module utils.context
"""

import os
import pytest

from silex_client.utils.context import Context
from silex_client.utils.enums import Status
from silex_client.action.loader import Loader


@pytest.fixture
def dummy_context() -> Context:
    """
    Return a context initialized in the test folder to work the configuration files
    that has been created only for test purpose
    """
    context = Context.get()
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    context.config.action_search_path.append(config_root)
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
        manual_action = loader.get_single_data()["publish"]
        assert len(resolved_action.commands["pre_action"]["commands"]) == len(
            manual_action["pre_action"]["commands"])
        assert len(resolved_action.commands["action"]["commands"]) == len(
            manual_action["action"]["commands"])
        assert len(resolved_action.commands["post_action"]["commands"]) == len(
            manual_action["post_action"]["commands"])
        loader.dispose()


def test_execute_action(dummy_context: Context):
    """
    Test the execution of all the commands in the 'foo' action from the config
    given by the dummy_context
    """
    action = dummy_context.get_action("publish")
    # Add some fake value to mimic the UI editing the parameters
    action.buffer.set_parameter("action", 0, "file_path", "/path/to/file")

    buffer = action.execute()
    for command in buffer:
        print(command.status)
    assert buffer.status is Status.COMPLETED
