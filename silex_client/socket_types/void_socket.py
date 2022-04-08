from silex_client.socket_types.socket_type import SocketType


class VoidSocket(SocketType):
    def get_default(self):
        return None
