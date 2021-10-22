from silex_client.core.context import Context
from silex_client.network.websocket import WebsocketConnection
from silex_client.core.event_loop import EventLoop
from silex_client.utils.authentification import authentificate_gazu

STARTUP_TASKS = [WebsocketConnection]


class Initializer:
    @staticmethod
    def start():
        authentificate_gazu()

        context = Context.get()

        # Initialize the event loop
        context.event_loop = EventLoop()
        context.event_loop.start()

        # Initialize the websocket connection
        context.ws_connection = WebsocketConnection(
            context.event_loop, context.metadata
        )
        context.ws_connection.start()

    @staticmethod
    def shutdown():
        pass
