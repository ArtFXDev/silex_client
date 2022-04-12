from silex_client.socket_types.socket_type import SocketType


class VoidSocket(SocketType[None]):
    def get_default(self):
        return None

    def cast(self, value):
        return None
