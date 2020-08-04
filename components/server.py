""" A server in a distributed system. """

import os
import sys
import time
import socket
import random
from multiprocessing import Process
from threading import Thread, Lock

from components.server_state import ServerState
import components.utils as utils

class Server:

    def __init__(self, identifier, port, server_hostports, interval,
                 active=False, verbose=True):
        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # server info
        self._identifier = identifier
        self._hostport = socket.gethostname() + ':' + str(port)
        self._server_hostports = server_hostports
        self._interval = interval
        self._active = active
        self._primary = False
        self._primary_index = None

        # bind sockets
        self._sock = socket.socket()
        self._sock.bind(utils.address(self._hostport))
        self._server_socks = [socket.socket() for hostport in server_hostports]
        self._connected = [False for hostport in server_hostports]

        # server state
        self._state = ServerState()
        self._log = []
        self._num_requests = 0
        self._ready = False
        self._lock = Lock()

        # server process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'Server {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _connect(self, index):
        try:
            sock = self._server_socks[index]
            server_hostport = self._server_hostports[index]
            sock.connect(utils.address(server_hostport))

            utils.send(sock, self._identifier, 0, 'server')
            identifier, number, _, state = utils.recv(sock)

            # make sure server is still connected
            if identifier is None:
                sock.close()
                self._server_socks[index] = socket.socket()
                self._connected[index] = False
            else:
                self._print(f'Connected to Server {identifier}')
                # update state
                if number > self._num_requests:
                    with self._lock:
                        self._print('Updating state')
                        self._state = state
                        self._num_requests = number
                        if self._log:
                            self._print('Clearing log')
                        for request in self._log:
                            self._state.update(int(request))
                        self._log = []
                        self._ready = True
                self._ready = True
                self._connected[index] = True
        except Exception:
            self._connected[index] = False


    def _handle_lfd(self, conn, lfd_identifier):
        self._print(f'Connection from LFD {lfd_identifier}')

        _, number, heartbeat, _ = utils.recv(conn)
        while heartbeat is not None:
            utils.send(conn, self._identifier, number, heartbeat)
            _, number, heartbeat, _ = utils.recv(conn)

        self._print(f'Connection closed by LFD {lfd_identifier}')


    def _handle_primary(self, conn):
        _, number, num_requests, checkpoint = utils.recv(conn)

        while checkpoint is not None:
            self._print(f'Received checkpoint (#{number}) {checkpoint}')

            if int(num_requests) > self._num_requests:
                with self._lock:
                    self._state = checkpoint
                    self._num_requests = int(num_requests)
                    for request in self._log:
                        self._state.update(int(request))
                    self._log = []

            try:
                utils.send(conn, self._identifier, number, 'ok')
                _, number, num_requests, checkpoint = utils.recv(conn)
            except Exception:
                with self._lock:
                    if self._primary_index is not None:
                        self._print('Connection closed by Primary')
                        self._connected[self._primary_index] = False
                        self._primary_index = None
                time.sleep(1 + random.random() * 5)
                self._elect()
                return

        with self._lock:
            if self._primary_index is not None:
                self._print('Connection closed by Primary')
                self._connected[self._primary_index] = False
                self._primary_index = None
        time.sleep(1 + random.random() * 5)
        self._elect()


    def _handle_backup(self, conn, identifier):
        number = 1
        while True:
            self._print(f'Sending checkpoint (#{number}) {self._state} to '
                        f'Server {identifier}')
            try:
                utils.send(conn, self._identifier, number, self._num_requests,
                           state=self._state)
                _, _, res, _ = utils.recv(conn)
            except Exception:
                res = None
            if res is None:
                self._print(f'Connection closed by Server {identifier}')
                return

            number += 1
            time.sleep(self._interval)


    def _handle_client(self, conn, client_identifier):
        self._print(f'Connection from Client {client_identifier}')

        _, number, request, _ = utils.recv(conn)
        while request is not None:
            self._print(f'Received (#{number}) {request} from Client '
                        f'{client_identifier}')

            with self._lock:
                if (not self._ready or (not self.is_active() and
                                        not self.is_primary())):
                    self._log.append(request)
                    self._print('Added request to log')
                    utils.send(conn, self._identifier, number, 'ok')
                else:
                    response = self._state.update(int(request))
                    self._num_requests += 1
                    self._print(f'Sending (#{number}) {response} to Client '
                                f'{client_identifier}')
                    utils.send(conn, self._identifier, number, response)

            _, number, request, _ = utils.recv(conn)

        self._print(f'Connection closed by Client {client_identifier}')


    def _run_active(self, conn, identifier, number, data):
        while True:
            # check connection type
            if data == 'lfd':
                utils.send(conn, self._identifier, number, 'server')
                self._handle_lfd(conn, identifier)
                return
            if data == 'client':
                utils.send(conn, self._identifier, number, 'server')
                self._handle_client(conn, identifier)
                return
            if data == 'server':
                utils.send(conn, self._identifier, self._num_requests,
                           'server', self._state)
            if data is None:
                return
            identifier, number, data, _ = utils.recv(conn)


    def _elect(self):
        for i in range(len(self._server_socks)):
            sock = self._server_socks[i]
            try:
                utils.send(sock, self._identifier, 0, 'elect')
                identifier, number, data, _ = utils.recv(sock)
                self._lock.acquire()
                if self._primary_index is not None:
                    self._lock.release()
                    return
                if data is not None and 'primary' in data:
                    self._primary = False
                    self._ready = False
                    self._primary_index = i
                    utils.send(sock, self._identifier, number,
                               'backup')
                    self._print('Primary: ' + identifier)
                    self._lock.release()
                    Thread(target=self._run_passive,
                           args=[sock, identifier, number, data]).start()
                    return
                if data == 'approve':
                    self._primary = True
                    self._ready = True
                    self._primary_index = None
                    utils.send(sock, self._identifier, number,
                               'primary|' + self._hostport)
                    self._print('Elected Primary')
                    self._lock.release()
                    Thread(target=self._run_passive,
                           args=[sock, identifier, number, data]).start()
                    return
                self._lock.release()
            except Exception:
                pass
        # no other servers have responded
        with self._lock:
            self._primary = True
            self._ready = True
            self._primary_index = None
        self._print('Default Primary')


    def _run_passive(self, conn, identifier, number, data):
        while True:
            # check connection type
            if data == 'lfd':
                utils.send(conn, self._identifier, number, 'server')
                self._handle_lfd(conn, identifier)
                return
            if data == 'client':
                utils.send(conn, self._identifier, number, 'server')
                self._handle_client(conn, identifier)
                return
            if data == 'server':
                utils.send(conn, self._identifier, self._num_requests,
                           'server', self._state)
            elif data == 'elect':
                with self._lock:
                    if not self.is_primary() and self._primary_index is None:
                        utils.send(conn, self._identifier, number, 'approve')
                    elif self._primary_index is not None:
                        utils.send(conn, self._identifier, number,
                                   'disapprove')
                    else:
                        utils.send(conn, self._identifier, number,
                                   'primary|' + self._hostport)
            elif data is not None and 'primary' in data:
                with self._lock:
                    if self._primary_index is None:
                        self._print('Primary: ' + identifier)
                    self._primary = False
                    self._ready = False
                    server_hostport = data.split('|')[1]
                    self._primary_index = self._server_hostports.index(
                        server_hostport
                    )
                utils.send(conn, self._identifier, number, 'backup')
                self._handle_primary(conn)
            elif data == 'backup':
                if self.is_primary():
                    self._handle_backup(conn, identifier)
                    return
            if data is None:
                return
            identifier, number, data, _ = utils.recv(conn)


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()
        for i, connected in enumerate(self._connected):
            if not connected:
                self._connect(i)
        self._elect()

        while True:
            for i, connected in enumerate(self._connected):
                if not connected:
                    self._connect(i)
            conn, _ = self._sock.accept()
            identifier, number, data, _ = utils.recv(conn)
            if self.is_active():
                Thread(target=self._run_active,
                       args=[conn, identifier, number, data]).start()
            else:
                Thread(target=self._run_passive,
                       args=[conn, identifier, number, data]).start()


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
            for i in range(len(self._server_socks)):
                if self._connected[i]:
                    self._server_socks[i].close()
                    self._server_socks[i] = socket.socket()


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport


    def is_active(self):
        return self._active


    def is_primary(self):
        return self._primary
