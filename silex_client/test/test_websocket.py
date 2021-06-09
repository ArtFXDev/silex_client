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

from silex_client.utils.context import context
from silex_client.utils.websocket import WebsocketConnection


@pytest.fixture
def pingpong_server():
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    async def pingpong(websocket, path):
        try:
            message = await websocket.recv()
            assert message == str(context.metadata)
        except (ConnectionClosed, ConnectionClosedError):
            asyncio.get_event_loop().stop()

        ping = "ping"
        try:
            await websocket.send(ping)
        except (ConnectionClosed, ConnectionClosedError):
            asyncio.get_event_loop().stop()

        try:
            pong = await websocket.recv()
            assert pong == "pong"
        except (ConnectionClosed, ConnectionClosedError):
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
def client():
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    return WebsocketConnection()


def test_websocket_pingpong(pingpong_server, client):
    """
    Test the message exchange between a dummy server and the client
    """
    pingpong_server.start()
    client.run_multithreaded()
    time.sleep(1)
    client.stop()
    pingpong_server.join()
    time.sleep(1)
