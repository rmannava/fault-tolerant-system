""" A client in a distributed system. """

import os
import sys
import time
import socket
import random
from multiprocessing import Process

import components.utils as utils

class Client:
    """ The Client class.

    Communicates via a TCP socket.
    """

    def __init__(self, identifier, server_hostport, interval, verbose=False):
        """ Returns a Client object.

        Opens a connection to the server hostport.

        Args:
            identifier: The int or string used to identify this client.
            server_port: The string hostport of the server that this this
                client should connect to.
            interval: The positive integer interval in seconds at which the
                client should make requests to the server.
            verbose: A boolean; if True the client will print info to stdout.
        """
        if not isinstance(identifier, str) and not isinstance(identifier, int):
            raise TypeError(f'identifier {identifier} has type '
                            '{type(identifier)}; must be int or str')
        if not isinstance(server_hostport, str):
            raise TypeError(f'server_hostport {server_hostport} has type '
                            '{type(server_hostport)}; must be str')
        if not isinstance(interval, int):
            raise TypeError(f'interval {interval} has type {type(interval)}; '
                            'must be int')
        if interval <= 0:
            raise ValueError(f'interval {interval} must be a positive value')
        if not isinstance(verbose, bool):
            raise TypeError(f'verbose {verbose} has type {type(verbose)}; must '
                            'be bool')

        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # client info
        self._identifier = identifier
        self._server_hostport = server_hostport
        self._interval = interval

        # create socket
        self._sock = socket.socket()

        # client process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'Client {self._identifier}: ' + comb_args, **kwargs, file=self._stdout)


    def _close_conn(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()
        self._sock = socket.socket()


    def _request(self, limit=None):
        self._print(f'Connecting to server at {self._server_hostport}')
        self._sock.connect(utils.address(self._server_hostport))

        utils.send(self._sock, self._identifier, 'connected')
        server_identifier, _ = utils.recv(self._sock)
        # make sure server is still connected
        if server_identifier is None:
            self._close_conn()
            self._print(f'Connection closed by server at {self._server_hostport}')
        self._print(f'Connected to Server {server_identifier}')

        num_requests = 0
        while limit is None or num_requests < int(limit):
            request = random.randint(1, 10)
            self._print(f'Sending {request} to Server {server_identifier}')
            utils.send(self._sock, self._identifier, request)
            num_requests += 1

            identifier, response = utils.recv(self._sock)
            self._print(f'Received {response} from Server {identifier}')

            time.sleep(self._interval)

        self._print(f'Completed {limit} request(s)')
        self._close_conn()
        self._print(f'Connection to Server {server_identifier} closed')


    def start(self, limit=None):
        self._process = Process(target=self._request, args=[limit])
        self._process.start()


    def stop(self):
        self._print('Stopping')
        if self._process is not None:
            self._process.terminate()
            self._close_conn()
            self._print('Client stopped')

    def is_running(self):
        return self._process.is_alive()

