""" A server in a distributed system. """

import os
import sys
import socket
from multiprocessing import Process
from threading import Thread

from components.server_state import ServerState
import components.utils as utils

class Server:
    """ The Server class.

    Communicates via a TCP socket.
    """

    def __init__(self, identifier, port, verbose=False):
        """ Returns a Server object.

        Binds the specified port.

        Args:
            identifier: The int or string used to identify this server.
            port: The int TCP port number this server should listen on.
            verbose: A boolean; if True the server will print info to stdout.
        """
        if not isinstance(identifier, str) and not isinstance(identifier, int):
            raise TypeError(f'identifier {identifier} has type '
                            '{type(identifier)}; must be int or str')
        if not isinstance(port, int):
            raise TypeError(f'port {port} has type {type(port)}; must be int')
        if not isinstance(verbose, bool):
            raise TypeError(f'verbose {verbose} has type {type(verbose)}; must '
                            'be bool')

        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # server info
        self._identifier = identifier
        self._hostport = socket.gethostname() + ':' + str(port)

        # bind socket
        sock = socket.socket()
        sock.bind(utils.address(self._hostport))
        self._sock = sock

        # server state
        self._state = ServerState()

        # server process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'Server {self._identifier}: ' + comb_args, **kwargs, file=self._stdout)


    def _handle_client(self, conn, client_identifier):
        self._print(f'Connection from Client {client_identifier}')

        _, request = utils.recv(conn)
        while request is not None:
            self._print(f'Received {request} from Client {client_identifier}')

            response = self._state.update(int(request))
            self._print(f'Sending {response} to Client {client_identifier}')
            utils.send(conn, self._identifier, response)

            _, request = utils.recv(conn)

        self._print(f'Connection closed by Client {client_identifier}')


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()

        while True:
            conn, _ = self._sock.accept()
            utils.send(conn, self._identifier, 'connected')
            client_identifier, _ = utils.recv(conn)
            # make sure client is still connected
            if client_identifier is not None:
                Thread(target=self._handle_client, args=[conn, client_identifier]).start()


    def start(self):
        self._process = Process(target=self._listen)
        self._process.start()


    def stop(self):
        self._print('Stopping')
        if self._process is not None:
            # stop serving requests
            self._process.terminate()

            # stop listening for connections
            self._sock.shutdown(socket.SHUT_RDWR)

            self._print('Server stopped')


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport
