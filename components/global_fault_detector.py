""" A global fault detector in a distributed system. """

import os
import sys
import socket
from multiprocessing import Process
from threading import Thread

import components.utils as utils

class GlobalFaultDetector:

    def __init__(self, identifier, port, rm_hostport, verbose=True):
        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # gfd info
        self._identifier = identifier
        self._hostport = socket.gethostname() + ':' + str(port)
        self._rm_hostport = rm_hostport

        # create sockets
        self._sock = socket.socket()
        self._sock.bind(utils.address(self._hostport))
        self._rm_sock = socket.socket()
        self._rm_connected = False

        # membership
        self._members = []

        # gfd process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'GFD {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _connect(self):
        try:
            self._print(f'Connecting to RM at {self._rm_hostport}')
            self._rm_sock.connect(utils.address(self._rm_hostport))

            utils.send(self._rm_sock, self._identifier, 0, 'gfd')
            rm_identifier, _, _, _ = utils.recv(self._rm_sock)
            # make sure rm is still connected
            if rm_identifier is None:
                self._rm_sock.close()
                self._rm_sock = socket.socket()
                self._print('Connection closed by RM at '
                            f'{self._rm_hostport}')
                self._rm_connected = False
            self._print(f'Connected to RM {rm_identifier}')
            self._rm_connected = True
        except Exception:
            self._rm_connected = False


    def _handle_lfd(self, conn, lfd_identifier):
        self._print(f'Connection from LFD {lfd_identifier}')

        _, _, message, _ = utils.recv(conn)
        while message is not None:
            if not self._rm_connected:
                self._connect()
            if message == 'add':
                self._members.append(lfd_identifier)
                self._print(f'Added member {lfd_identifier}')
                self._print(f'Current members: {self._members}')
                if self._rm_connected:
                    utils.send(self._rm_sock, lfd_identifier, 0, 'add')
            elif message == 'remove':
                self._members.remove(lfd_identifier)
                self._print(f'Removed member {lfd_identifier}')
                self._print(f'Current members: {self._members}')
                if self._rm_connected:
                    utils.send(self._rm_sock, lfd_identifier, 0, 'remove')
            _, _, message, _ = utils.recv(conn)

        self._print(f'Connection closed by LFD {lfd_identifier}')
        if lfd_identifier in self._members:
            self._members.remove(lfd_identifier)
            self._print(f'Removed member {lfd_identifier}')
            self._print(f'Current members: {self._members}')


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()

        # connect to rm
        self._connect()

        while True:
            conn, _ = self._sock.accept()
            identifier, number, data, _ = utils.recv(conn)
            utils.send(conn, self._identifier, number, 'gfd')
            # check for lfd
            if data == 'lfd':
                Thread(target=self._handle_lfd, args=[conn, identifier]).start()


    def start(self):
        self._process = Process(target=self._listen)
        self._process.start()


    def stop(self):
        self._print('Stopping GFD')
        if self._process is not None:
            self._process.terminate()
            self._sock.shutdown(socket.SHUT_RDWR)


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport
