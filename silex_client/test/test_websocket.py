"""
@author: TD gang

Unit testing functions for the module utils.websocket
"""
import asyncio
import time
from threading import Thread

import pytest
import websockets

from silex_client.utils.websocket import WebsocketConnection
from silex_client.utils.context import context


@pytest.fixture
def server():
    async def time(websocket, path):
        try:
            message = await websocket.recv()
            assert message == str(context.metadata)
        except websockets.ConnectionClosed:
            asyncio.get_event_loop().stop()

        ping = "ping"
        try:
            await websocket.send(ping)
        except websockets.ConnectionClosed:
            asyncio.get_event_loop().stop()

        try:
            pong = await websocket.recv()
            assert pong == "pong"
        except websockets.ConnectionClosed:
            asyncio.get_event_loop().stop()
        
        asyncio.get_event_loop().stop()

    def job():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = websockets.serve(time, "127.0.0.1", 8080)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    return Thread(target=lambda:job())

@pytest.fixture
def client():
    return WebsocketConnection()

def test_websocket_pingpong(server, client):
    pass
    server.start()
    client.run_multithreaded()
    time.sleep(3)
    client.stop()
    server.join(3)
    assert False
