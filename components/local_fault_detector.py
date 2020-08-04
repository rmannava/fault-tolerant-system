""" A local fault detector in a distributed system. """

import os
import sys
import time
import socket
from multiprocessing import Process

import components.utils as utils

class LocalFaultDetector:

    def __init__(self, identifier, server_hostport, gfd_hostport, interval,
                 verbose=True):
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


    def _connect(self):
        try:
            self._print(f'Connecting to server at {self._server_hostport}')
            self._server_sock.connect(utils.address(self._server_hostport))

            utils.send(self._server_sock, self._identifier, 0, 'lfd')
            server_identifier, _, _, _ = utils.recv(self._server_sock)
            # make sure server is still connected
            if server_identifier is None:
                self._server_sock.close()
                self._server_sock = socket.socket()
                self._print('Connection closed by server at '
                            f'{self._server_hostport}')
                return False, server_identifier
            self._print(f'Connected to Server {server_identifier}')
            return True, server_identifier
        except Exception:
            return False, None


    def _heartbeat(self):
        # connect to server
        connected, server_identifier = self._connect()

        # connect to gfd
        self._print(f'Connecting to GFD at {self._gfd_hostport}')
        self._gfd_sock.connect(utils.address(self._gfd_hostport))

        utils.send(self._gfd_sock, self._identifier, 0, 'lfd')
        gfd_identifier, _, _, _ = utils.recv(self._gfd_sock)
        # make sure gfd is still connected
        if gfd_identifier is None:
            self._gfd_sock.close()
            self._gfd_sock = socket.socket()
            self._print('Connection closed by GFD at '
                        f'{self._gfd_hostport}')
            return
        self._print(f'Connected to GFD {gfd_identifier}')
        member = False

        number = 1
        while True:
            if not connected:
                connected, server_identifier = self._connect()
            if connected:
                self._print(f'Sending heartbeat #{number} to Server '
                            f'{server_identifier}')
                utils.send(self._server_sock, self._identifier, number,
                           'heartbeat')

                _, res_number, response, _ = utils.recv(self._server_sock)
                if response is None:
                    self._print(f'No response from Server {server_identifier}')
                    self._server_sock.close()
                    self._server_sock = socket.socket()
                    connected = False
                    if member:
                        self._print(f'Alerting GFD')
                        utils.send(self._gfd_sock, self._identifier, 0,
                                   'remove')
                        member = False
                else:
                    self._print(f'Heartbeat response #{res_number} from Server '
                                f'{server_identifier}')
                    if not member:
                        self._print(f'Registering membership with GFD')
                        utils.send(self._gfd_sock, self._identifier, 0, 'add')
                        member = True

                number += 1
            time.sleep(self._interval)


    def start(self):
        self._process = Process(target=self._heartbeat)
        self._process.start()


    def stop(self):
        self._print('Stopping LFD')
        if self._process is not None:
            self._process.terminate()
            self._server_sock.close()
            self._server_sock = socket.socket()
            self._gfd_sock.close()
            self._gfd_sock = socket.socket()


    def is_running(self):
        return self._process.is_alive()
