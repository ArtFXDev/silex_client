import os
import pprint

import pytest

from silex_dcc.utils.config import Config


@pytest.fixture
def dummy_config():
    """
    Return a config initialized in the test folder to work the configuration files that has been created only for test purpose
    """
    config_root_path = os.path.dirname(__file__)
    return Config(config_root_path)


@pytest.fixture
def maya_config():
    """
    Return a config initialized with the real configuration folder to work with the real dcc configuration files
    """
    return Config()


def test_resolve_config(dummy_config):
    """
    Test the resolving of a configuration for the action 'foo' and the task 'task_a' with a dummy config file
    """
    resolved_config = dummy_config.resolve_config("dcc", "foo", "task_a")
    # Pretty print the resolved config
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(resolved_config)

    # Make sure the inheritance has been resolved corectly
    assert len(resolved_config["action"]) == 3
    assert len(resolved_config["post"]) == 3
    assert resolved_config["action"][1][
        "string"] == "printing A from dcc/foo/task_a"
    assert resolved_config["post"][1]["command"] == "test.empty"
    assert resolved_config["pre"][0]["command"] == "test.empty"


def test_resolve_none_existing_action(dummy_config):
    """
    Test the resolving of a configuration for the non existing action 'foobar' and a task 'task_a' with a dummy config file
    """
    resolved_config = dummy_config.resolve_config("dcc", "foobar", "task_a")
    # Pretty print the resolved config
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(resolved_config)

    # Make sure the the config is empty
    assert resolved_config == {"post": [], "action": [], "pre": []}


def test_resolve_none_existing_task(dummy_config):
    """
    Test the resolving of a configuration for the action 'foo' and a non existing task 'task_z' with a dummy config file
    """
    resolved_config = dummy_config.resolve_config("dcc", "foo", "task_z")
    # Pretty print the resolved config
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(resolved_config)

    # Make sure the config only has the config from the action
    assert len(resolved_config["action"]) == 2
    assert len(resolved_config["pre"]) == 3
    assert resolved_config["action"][0]["string"] == "printing A from dcc/foo"
    assert resolved_config["post"][0]["string"] == "printing C from dcc/foo"


def test_resolve_none_existing_file(dummy_config):
    """
    Test the resolving of a configuration with a non existing config file
    """
    with pytest.raises(FileNotFoundError):
        dummy_config.resolve_config("none", "foo", "task_a")
