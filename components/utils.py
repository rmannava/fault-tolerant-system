""" Utility functions. """

from components.message import Message

RECV_SIZE = 1024

def send(sock, identifier, number, data):
    sock.sendall(Message(identifier, number, data).encode())


def recv(sock):
    encoded = sock.recv(RECV_SIZE)
    message = Message(encoded=encoded)
    if message.valid:
        return message.identifier, message.number, message.data
    return None, None, None


def hostport(address_string):
    return address_string[0] + ':' + str(address_string[1])


def address(hostport_string):
    parts = hostport_string.split(':')
    return (parts[0], int(parts[1]))
