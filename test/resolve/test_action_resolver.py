from pathlib import Path
from typing import Any, List, Tuple

import pytest

from silex_client.resolve.loader import Loader
from silex_client.resolve.action_resolver import ActionResolver


@pytest.fixture
def resolver() -> ActionResolver:
    root_dir = Path(__file__).parent / "actions"
    config_search_path = [
        root_dir / "root-a",
        root_dir / "root-b",
    ]

    return ActionResolver(config_search_path)


load_actions_data: List[Tuple[Path, Any]] = [
    (
        Path(__file__).parent / "actions" / "root-b" / "namespace-a" / "baz.yml",
        {"baz": {"aa": 349, "bb": {"cc": 430}}},
    ),
    (
        Path(__file__).parent / "actions" / "root-b" / "namespace-a" / "qux.yml",
        {"qux": {"aa": {"dd": 330, "ee": 203}}},
    ),
]


@pytest.mark.parametrize("load_action_data", load_actions_data)
def test_load_action(resolver: ActionResolver, load_action_data: Tuple[Path, Any]):
    action_path, action_assert = load_action_data

    with open(action_path, "r", encoding="utf-8") as action_data:
        loader = Loader(action_data, action_path, resolver)
        action = loader.get_single_data()
        loader.dispose()

        assert action == action_assert


resolve_actions_data: List[Tuple[str, Any]] = [
    (
        "namespace-a::baz",
        {"baz": {"aa": 349, "bb": {"cc": 430}}},
    ),
    (
        "namespace-a::qux",
        {"qux": {"aa": {"dd": 330, "ee": 203}}},
    ),
]


@pytest.mark.parametrize("resolve_action_data", resolve_actions_data)
def test_resolve_action(resolver: ActionResolver, resolve_action_data: Tuple[str, Any]):
    action_name, action_assert = resolve_action_data

    action = resolver.resolve_config(action_name)
    assert action == action_assert


resolve_actions_inheritance: List[Tuple[str, Any]] = [
    (
        "namespace-a::foo",
        [
            ["foo", "aa", "dd"],
            ["foo", "bb"],
            ["foo", "steps", "action", "commands", "first_a"],
            ["foo", "steps", "action", "commands", "first_b"],
            ["foo", "steps", "action", "commands", "second_a"],
        ],
    ),
    (
        "namespace-a::bar",
        [
            ["bar", "aa", "dd"],
            ["bar", "bb"],
            ["bar", "steps", "action", "commands", "first_a"],
            ["bar", "steps", "action", "commands", "first_b"],
            ["bar", "steps", "post_action", "commands", "close_action_a"],
            ["bar", "steps", "pre_action", "commands", "initalize_action_a"],
            ["bar", "steps", "action", "label"],
        ],
    ),
]


@pytest.mark.parametrize("resolve_action_inheritance", resolve_actions_inheritance)
def test_resolve_inheritance(
    resolver: ActionResolver, resolve_action_inheritance: Tuple[str, Any]
):
    action_name, action_asserts = resolve_action_inheritance

    action = resolver.resolve_config(action_name, traceback=[])
    assert action is not None

    for action_assert in action_asserts:
        action_check = action
        for key in action_assert:
            assert key in action_check
            action_check = action_check[key]
