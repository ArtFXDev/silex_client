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

MESSAGES = [
    "message_A", "message_B", "message_C", "message_C", "message_D",
    "message_E", "message_F", "message_G", "message_H", "message_I"
]


def pingpong_server():
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    async def pingpong(websocket, path):
        # assert path == WebsocketConnection.parameters_to_url(
        # "/",
        # Context.get().metadata)

        try:
            print("CCCCCCCCCCCCCC")
            await websocket.send("ping")
        except (ConnectionClosed, ConnectionClosedError) as e:
            asyncio.get_event_loop().stop()

        try:
            print("DDDDDDDDDDDDDDDD")
            pong = await websocket.recv()
            print("EEEEEEEEEEEEEEEE")
            print(pong)
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


def queue_server():
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    async def queue(websocket, path):
        print(path)
        print(
            WebsocketConnection.parameters_to_url("/",
                                                  Context.get().metadata))
        assert path == WebsocketConnection.parameters_to_url(
            "/",
            Context.get().metadata)

        for message in MESSAGES:
            try:
                answer = await websocket.recv()
                assert answer == message
            except (ConnectionClosed, ConnectionClosedError):
                asyncio.get_event_loop().stop()

        asyncio.get_event_loop().stop()

    def job():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        start_server = server.serve(queue, "127.0.0.1", 8080)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    return Thread(target=job)


def client():
    """
    Return a server that will wait for the metadata, send a a ping and wait for a pong
    """
    return Context.get().ws_connection


def test_websocket_pingpong(pingpong_server, client):
    """
    Test a pingpong exchange between a dummy server and the client
    """
    pingpong_server.start()
    client.run_multithreaded()
    # Wait a bit to let the exchange happend
    time.sleep(1)
    # Stop the server and the client
    client.stop()
    pingpong_server.join()


def test_websocket_echo(queue_server, client):
    """
    Test the message sending queue
    """
    queue_server.start()
    client.run_multithreaded()
    # Wait a bit to let the exchange happend
    time.sleep(1)
    # Stop the server and the client
    client.stop()
    queue_server.join()
