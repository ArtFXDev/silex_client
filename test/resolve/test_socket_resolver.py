from pathlib import Path
from typing import List, Tuple

import pytest
import inspect

from silex_client.resolve.socket_resolver import SocketResolver


@pytest.fixture
def resolver() -> SocketResolver:
    root_dir = Path(__file__).parent / "sockets"
    config_search_path = [
        root_dir / "root_a",
        root_dir / "root_b",
    ]

    return SocketResolver(config_search_path)


resolve_sockets_data: List[Tuple[str, List[str]]] = [
    ("FooSocket", ["foo", "root_a"]),
    ("BarSocket", ["bar", "root_a"]),
    ("BazSocket", ["baz", "root_b"]),
]


@pytest.mark.parametrize("resolve_socket_data", resolve_sockets_data)
def test_resolve_action(
    resolver: SocketResolver, resolve_socket_data: Tuple[str, List[str]]
):
    socket_name, socket_asserts = resolve_socket_data
    socket = resolver.resolve_definition(socket_name)

    assert socket is not None
    assert socket.__name__ == socket_name

    socket_path = Path(inspect.getfile(socket))
    for socket_assert in socket_asserts:
        assert socket_path.stem == socket_assert
        socket_path = socket_path.parent
