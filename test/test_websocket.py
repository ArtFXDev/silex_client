"""
@author: TD gang

Unit testing functions for the module networK.websocket
"""

import asyncio
import threading
import aiohttp

import pytest
import socketio
from aiohttp import web, test_utils

from silex_client.core.context import Context
from silex_client.network.websocket import WebsocketConnection

from .mocks.websocket import DCCNamespace, ActionNamespace
from .test_config import dummy_config
from .test_action import dummy_context

# Get an unused port
TEST_PORT = test_utils.get_unused_port_socket("127.0.0.1").getsockname()[-1]


@pytest.fixture
def dummy_server() -> threading.Thread:
    """
    Return a function to start a server that will listen on the namespaces /dcc and /dcc/action
    """

    server = socketio.AsyncServer(async_mode="aiohttp")
    app = web.Application()

    server.register_namespace(DCCNamespace("/dcc", app))
    server.register_namespace(ActionNamespace("/dcc/action", app))
    server.attach(app)
    runner = web.AppRunner(app)

    def start_server(runner: web.AppRunner) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, host="127.0.0.1", port=TEST_PORT)
        loop.run_until_complete(site.start())
        loop.run_forever()

    return threading.Thread(target=start_server, daemon=True, args=(runner,))


def test_connection_initialization(
    dummy_context: Context, dummy_server: threading.Thread
):
    """
    Test if the context is sent on initialization
    """
    dummy_server.start()

    # Restart the services on a new port
    dummy_context.stop_services()
    dummy_context.ws_connection = WebsocketConnection(
        f"ws://127.0.0.1:{TEST_PORT}", dummy_context
    )
    dummy_context.start_services()

    assert dummy_context.ws_connection.is_running
