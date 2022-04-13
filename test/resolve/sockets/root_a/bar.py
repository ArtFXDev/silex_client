from silex_client.graph.socket_types.socket_type import SocketType


class BarSocket(SocketType[str]):
    def get_default(self):
        return "bar"

    def cast(self, value):
        if isinstance(value, str):
            return value

        return str(value)
