"""
@author: TD gang

Unit testing functions for the module utils.context
"""

import pytest
import os
import pprint

from silex_client.utils.context import Context
from silex_client.action.loader import Loader


@pytest.fixture
def dummy_context():
    """
    Return a context initialized in the test folder to work the configuration files
    that has been created only for test purpose
    """
    context = Context.get()
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    context.config.config_search_path.append(config_root)
    # Change the context's metadata with test values
    context.metadata = {
        "dcc": "dcc",
        "task": "task_a",
    }
    # Little hack to make sure the context will not try to update itself
    context.is_outdated = False
    return context


def test_get_action(dummy_context: Context):
    """
    Test the execution of all the commands in the 'foo' action from the config
    given by the dummy_context
    """
    resolved_action = dummy_context.get_action("publish")
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    action_file = os.path.join(config_root, "publish.yml")

    # Load the file manualy and check if it correspond to the resolved file
    with open(action_file, "r") as config_data:
        loader = Loader(config_data, tuple(config_root))
        assert resolved_action == loader.get_single_data()
        loader.dispose()
