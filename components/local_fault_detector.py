""" A local fault detector in a distributed system. """

import os
import sys
import time
import socket
from multiprocessing import Process

import components.utils as utils

class LocalFaultDetector:
    """ The LocalFaultDetector class.

    Communicates via a TCP socket.
    """

    def __init__(self, identifier, server_hostport, gfd_hostport, interval,
                 verbose=True):
        """ Creates a LocalFaultDetector object.

        Opens a connection to the server hostport and GFD hostport.

        Args:
            identifier: The int or string used to identify this LFD.
            server_port: The string hostport of the server that this LFD should
                connect to.
            gfd_port: The string hostport of the GFD that this LFD should
                connect to.
            interval: The positive integer interval in seconds at which the
                LFD should send heartbeats to the server.
            verbose: A boolean; if True the LFD will print info to stdout.
        """
        # validate arguments
        if not isinstance(identifier, str) and not isinstance(identifier, int):
            raise TypeError(f'identifier {identifier} has type '
                            f'{type(identifier)}; must be int or str')
        if not isinstance(server_hostport, str):
            raise TypeError(f'server_hostport {server_hostport} has type '
                            f'{type(server_hostport)}; must be str')
        if not isinstance(gfd_hostport, str):
            raise TypeError(f'gfd_hostport {gfd_hostport} has type '
                            f'{type(gfd_hostport)}; must be str')
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

        # lfd info
        self._identifier = identifier
        self._server_hostport = server_hostport
        self._gfd_hostport = gfd_hostport
        self._interval = interval

        # create sockets
        self._server_sock = socket.socket()
        self._gfd_sock = socket.socket()

        # lfd process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'LFD {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _close_conns(self):
        self._server_sock.close()
        self._server_sock = socket.socket()
        self._gfd_sock.close()
        self._gfd_sock = socket.socket()


    def _heartbeat(self):
        # connect to server
        self._print(f'Connecting to server at {self._server_hostport}')
        self._server_sock.connect(utils.address(self._server_hostport))

        utils.send(self._server_sock, self._identifier, 0, 'lfd')
        server_identifier, _, _, _ = utils.recv(self._server_sock)
        # make sure server is still connected
        if server_identifier is None:
            self._close_conns()
            self._print('Connection closed by server at '
                        f'{self._server_hostport}')
            return
        self._print(f'Connected to Server {server_identifier}')

        # connect to gfd
        self._print(f'Connecting to GFD at {self._gfd_hostport}')
        self._gfd_sock.connect(utils.address(self._gfd_hostport))

        utils.send(self._gfd_sock, self._identifier, 0, 'lfd')
        gfd_identifier, _, _, _ = utils.recv(self._gfd_sock)
        # make sure gfd is still connected
        if gfd_identifier is None:
            self._close_conns()
            self._print('Connection closed by GFD at '
                        f'{self._gfd_hostport}')
            return
        self._print(f'Connected to GFD {gfd_identifier}')
        self._print(f'Registering membership')
        utils.send(self._gfd_sock, self._identifier, 0, 'add')

        number = 1
        while True:
            self._print(f'Sending heartbeat #{number} to Server '
                        f'{server_identifier}')
            utils.send(self._server_sock, self._identifier, number, 'heartbeat')

            _, res_number, response, _ = utils.recv(self._server_sock)
            if response is None:
                self._print(f'No response from Server {server_identifier}')
                self._print(f'Alerting GFD')
                utils.send(self._gfd_sock, self._identifier, 0, 'remove')
                self._print('Stopping LFD')
                self._close_conns()
                return
            self._print(f'Heartbeat response #{res_number} from Server '
                        f'{server_identifier}')

            number += 1
            time.sleep(self._interval)


    def start(self):
        self._process = Process(target=self._heartbeat)
        self._process.start()


    def stop(self):
        self._print('Stopping LFD')
        if self._process is not None:
            self._process.terminate()
            self._close_conns()


    def is_running(self):
        return self._process.is_alive()
