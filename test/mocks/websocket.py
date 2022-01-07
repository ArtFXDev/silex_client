import socketio
from aiohttp import web


class DCCNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace: str, app: web.Application):
        super().__init__(namespace)
        self.app = app

    async def on_connect(self, sid, environ):
        return {"status": 200}

    async def on_initialization(self, sid, environ):
        return {"status": 200}

    async def on_disconnect(self, sid, environ):
        return {"status": 200}


class ActionNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace: str, app: web.Application):
        super().__init__(namespace)
        self.app = app

    async def query(self, sid, environ):
        return {"status": 200}

    async def update(self, sid, environ):
        return {"status": 200}

    async def on_initialization(self, sid, environ):
        return {"status": 200}
