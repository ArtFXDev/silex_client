from silex_client.graph.socket_types.socket_type import SocketType


class FooSocket(SocketType[int]):
    def get_default(self):
        return 0

    def cast(self, value):
        if isinstance(value, int):
            return value

        return int(value)
