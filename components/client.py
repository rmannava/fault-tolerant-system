""" A client in a distributed system. """

import os
import sys
import time
import socket
import random
from multiprocessing import Process

import components.utils as utils

class Client:

    def __init__(self, identifier, server_hostports, interval, verbose=True):
        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # client info
        self._identifier = identifier
        self._server_hostports = server_hostports
        self._interval = interval
        self._connected = [False for i in range(len(server_hostports))]

        # create sockets for each server
        self._socks = [socket.socket() for i in range(len(server_hostports))]

        # client process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'Client {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _close_conns(self):
        for i in range(len(self._socks)):
            if self._connected[i]:
                self._connected[i] = False
                self._socks[i].close()
                self._socks[i] = socket.socket()


    def _connect(self, index):
        try:
            sock = self._socks[index]
            server_hostport = self._server_hostports[index]
            self._print(f'Connecting to server at {server_hostport}')
            sock.connect(utils.address(server_hostport))

            utils.send(sock, self._identifier, 0, 'client')
            server_identifier, _, _, _ = utils.recv(sock)

            # make sure server is still connected
            if server_identifier is None:
                sock.close()
                self._socks[index] = socket.socket()
                self._print('Connection closed by server at '
                            f'{server_hostport}')
                self._connected[index] = False
            else:
                self._print(f'Connected to Server {server_identifier}')
                self._connected[index] = True
            return server_identifier
        except Exception:
            self._connected[index] = False
            return ''


    def _request(self, limit=None):
        server_identifiers = ['' for i in range(len(self._socks))]
        # connect to each server
        for i in range(len(self._socks)):
            server_identifiers[i] = self._connect(i)
        num_requests = 0
        while limit is None or num_requests < int(limit):
            num_requests += 1

            if not any(self._connected):
                self._print(f'Stopping client after {num_requests-1} '
                            'successful request(s)')
                self._close_conns()
                return

            # send request to each server
            request = random.randint(1, 10)
            response = None
            for i in range(len(self._socks)):
                if not self._connected[i]:
                    self._connect(i)
                if self._connected[i]:
                    sock = self._socks[i]
                    self._print(f'Sending (#{num_requests}) {request} to '
                                f'Server {server_identifiers[i]}')
                    utils.send(sock, self._identifier, num_requests, request)

                    _, res_number, res, _ = utils.recv(sock)
                    if res is None:
                        self._print('Connection closed by Server '
                                    f'{server_identifiers[i]}')
                        sock.close()
                        self._socks[i] = socket.socket()
                        self._connected[i] = False
                    elif res != 'ok':
                        if response is None:
                            response = res
                            self._print(f'Received (#{res_number}) {res} from '
                                        f'Server {server_identifiers[i]}')
                        else:
                            self._print(f'Received (#{res_number}-duplicate) '
                                        f'{res} from Server '
                                        f'{server_identifiers[i]}')

            time.sleep(self._interval)

        self._print(f'Completed {num_requests} request(s)')
        self._close_conns()
        for i, identifier in enumerate(server_identifiers):
            if self._connected[i]:
                self._print(f'Connection to Server {identifier} closed')


    def start(self, limit=None):
        self._process = Process(target=self._request, args=[limit])
        self._process.start()


    def stop(self):
        self._print('Stopping client')
        if self._process is not None:
            self._process.terminate()
            self._close_conns()


    def is_running(self):
        return self._process.is_alive()
