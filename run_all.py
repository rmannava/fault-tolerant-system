#!/usr/bin/python3

import time

from components.server import Server
from components.client import Client

if __name__ == '__main__':
    server = Server(1, 5000, True)
    server.start()

    client_1 = Client(1, server.hostport(), 2, True)
    client_1.start(1)
