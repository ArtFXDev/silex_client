"""
@author: TD gang

Unit testing functions for the module utils.config
"""

import os

import pytest

from silex_client.resolve.config import Config


@pytest.fixture
def dummy_config():
    """
    Return a config initialized in the test folder to work the configuration
    files that has been created only for test purpose
    """
    config_root = os.path.join(os.path.dirname(__file__), "config", "action")
    return Config(config_root)


def test_resolve_action(dummy_config: Config):
    """
    Test the resolving of a configuration for the action 'foo' and the task 'task_a'
    with a dummy config file
    """
    resolved_action = dummy_config.resolve_action("publish")

    # Make sure the inheritance has been resolved corectly
    assert isinstance(resolved_action, dict) == True
    assert "publish" in resolved_action.keys()
    assert set(resolved_action["publish"]["steps"].keys()) == set(
        ["pre_action", "action", "post_action"]
    )
    assert len(resolved_action["publish"]["steps"]["pre_action"]) == 3


def test_resolve_non_existing_action(dummy_config):
    """
    Test the resolving of a configuration for the non existing action 'foobar' and
    a task 'task_a' with a dummy config file
    """
    resolved_action = dummy_config.resolve_action("fix_maya")

    # Make sure the the config is empty
    assert resolved_action == {}
