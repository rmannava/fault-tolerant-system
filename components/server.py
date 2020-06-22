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

    def __init__(self, identifier, port, verbose=True):
        """ Creates a Server object.

        Binds the specified port.

        Args:
            identifier: The int or string used to identify this server.
            port: The int TCP port number this server should listen on.
            verbose: A boolean; if True the server will print info to stdout.
        """
        # validate arguments
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


    def _handle_lfd(self, conn, lfd_identifier):
        self._print(f'Connection from LFD {lfd_identifier}')

        _, number, heartbeat = utils.recv(conn)
        while heartbeat is not None:
            utils.send(conn, self._identifier, number, heartbeat)
            _, number, heartbeat = utils.recv(conn)

        self._print(f'Connection closed by LFD {lfd_identifier}')


    def _handle_client(self, conn, client_identifier):
        self._print(f'Connection from Client {client_identifier}')

        _, number, request = utils.recv(conn)
        while request is not None:
            self._print(f'Received (#{number}) {request} from Client '
                        f'{client_identifier}')

            response = self._state.update(int(request))
            self._print(f'Sending (#{number}) {response} to Client '
                        f'{client_identifier}')
            utils.send(conn, self._identifier, number, response)

            _, number, request = utils.recv(conn)

        self._print(f'Connection closed by Client {client_identifier}')


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()

        while True:
            conn, _ = self._sock.accept()
            identifier, number, data = utils.recv(conn)
            utils.send(conn, self._identifier, number, 'server')
            # check for lfd/client
            if data == 'lfd':
                Thread(target=self._handle_lfd, args=[conn, identifier]).start()
            elif data == 'client':
                Thread(target=self._handle_client, args=[conn, identifier]).start()


    def start(self):
        self._process = Process(target=self._listen)
        self._process.start()


    def stop(self):
        self._print('Stopping server')
        if self._process is not None:
            # stop serving requests
            self._process.terminate()

            # stop listening for connections
            self._sock.shutdown(socket.SHUT_RDWR)


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport
