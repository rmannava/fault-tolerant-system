""" Utility functions. """

from components.message import Message
from components.server_state import ServerState

RECV_SIZE = 4096

def send(sock, identifier, number, data=None, state=None):
    sock.sendall(Message(identifier, number, data, state).encode())


def recv(sock):
    encoded = sock.recv(RECV_SIZE)
    message = Message(encoded=encoded)
    if message.valid:
        if message.state is not None:
            message.state = ServerState(message.state)
        return (message.identifier, int(message.number), message.data,
                message.state)
    return None, None, None, None


def hostport(address_string):
    return address_string[0] + ':' + str(address_string[1])


def address(hostport_string):
    parts = hostport_string.split(':')
    return (parts[0], int(parts[1]))
