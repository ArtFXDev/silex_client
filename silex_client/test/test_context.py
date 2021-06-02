import os

import pytest

from silex_client.utils.context import Context


@pytest.fixture
def dummy_context():
    """
    Return a context initialized in the test folder to work the configuration files that has been created only for test purpose
    """
    config_root_path = os.path.dirname(__file__)
    context = Context()
    context.config.config_root = os.path.join(config_root_path, "config")
    # Change the context's metadata with test values
    context.metadata = {
        "dcc": "dcc",
        "task": "task_a",
    }
    # Little hack to make sure the context will not try to update itself
    context.is_outdated = False
    return context


def test_execute_action(dummy_context):
    dummy_context.execute_action("foo")
