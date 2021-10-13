"""
@author: TD gang

Unit testing functions for the module networK.websocket
"""

import asyncio
import os
import threading
import time

import pytest
import socketio
from aiohttp import web

from silex_client.core.context import Context


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


@pytest.fixture
def dummy_server() -> threading.Thread:
    """
    Return a function to start a server that will listen on the namespaces /dcc and /dcc/action
    """

    def start_server() -> None:
        server = socketio.AsyncServer(async_mode="aiohttp")
        app = web.Application()

        class DCCNamespace(socketio.AsyncNamespace):
            def __init__(self, namespace: str, app: web.Application):
                super().__init__(namespace)
                self.app = app

            async def on_connect(self, sid, environ):
                pass

            async def on_initialization(self, sid, environ):
                pass

            async def on_disconnect(self, sid):
                pass

        class ActionNamespace(socketio.AsyncNamespace):
            async def query(self, sid, environ):
                pass

            async def update(self, sid):
                pass

        server.register_namespace(DCCNamespace("/dcc", app))
        server.register_namespace(ActionNamespace("/dcc/action"))
        server.attach(app)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        web.run_app(app, host="127.0.0.1", port=5118)

    return threading.Thread(target=start_server, daemon=True)


def wip_test_connection_initialization(
    dummy_context: Context, dummy_server: threading.Thread
):
    """
    Test if the context is sent on initialization
    """
    dummy_server.start()
    dummy_context.event_loop.start()
    dummy_context.ws_connection.start()

    assert dummy_context.ws_connection.is_running
