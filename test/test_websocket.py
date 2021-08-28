"""
@author: TD gang

Unit testing functions for the module utils.websocket
"""
import asyncio
import time
from threading import Thread

import pytest
from websockets import server
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

from silex_client.utils.context import Context
from silex_client.network.websocket import WebsocketConnection

MESSAGES = (f"message_{index}" for index in range(100))


@pytest.fixture
def pingpong_server() -> Thread:
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    async def pingpong(websocket, path):
        assert path == WebsocketConnection.parameters_to_url(
            "/",
            Context.get().metadata)

        try:
            await websocket.send("ping")

            pong = await asyncio.wait_for(websocket.recv(), 1)
            assert pong == "pong"
        except (ConnectionClosed, ConnectionClosedError, TimeoutError) as e:
            asyncio.get_event_loop().stop()

        asyncio.get_event_loop().stop()

    def job():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = server.serve(pingpong, "127.0.0.1", 8080)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    return Thread(target=job)


@pytest.fixture
def client() -> WebsocketConnection:
    """
    Return a client initialised on the current context
    """
    return Context.get().ws_connection


# Disabled for now
# TODO: Find the proper way to use async with pytest
def _test_websocket_pingpong(pingpong_server: Thread,
                            client: WebsocketConnection):
    """
    Test a pingpong exchange between a dummy server and the client
    """
    pingpong_server.start()
    client.run_multithreaded()
    # Wait a bit to let the exchange happend
    time.sleep(5)
    # Stop the server and the client
    client.stop()
    pingpong_server.join()
