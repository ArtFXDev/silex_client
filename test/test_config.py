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
    config_root_a = os.path.join(os.path.dirname(__file__), "config_a")
    config_root_b = os.path.join(os.path.dirname(__file__), "config_b")
    return Config([config_root_a, config_root_b])


def test_resolve_action(dummy_config: Config):
    """
    Test the resolving of a configuration for the action 'foo' and the task 'task_a'
    with a dummy config file
    """
    resolved_action = dummy_config.resolve_action("foo", category="test")

    # Make sure the inheritance has been resolved corectly
    assert resolved_action is not None
    assert "foo" in resolved_action.keys()
    assert set(resolved_action["foo"]["steps"].keys()) == set(
        ["pre_action", "action", "post_action"]
    )
    assert len(resolved_action["foo"]["steps"]["pre_action"]) == 3
    assert len(resolved_action["foo"]["steps"]["pre_action"]["commands"]) == 2
    assert len(resolved_action["foo"]["steps"]["action"]["commands"]) == 3


def test_resolve_non_existing_action(dummy_config):
    """
    Test the resolving of a configuration for the non existing action 'foobar' and
    a task 'task_a' with a dummy config file
    """
    resolved_action = dummy_config.resolve_action("fix_maya")

    # Make sure the the config is empty
    assert resolved_action is None
