import socketio


class WebsocketFrontEventNamespace(socketio.AsyncClientNamespace):
    """
    Special namespace /front-event to send custom events to the front-end
    Useful for redirecting, refreshing data or firing animations
    """

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass
