""" A replication manager in a distributed system. """

import os
import sys
import socket
from multiprocessing import Process
from threading import Thread

import components.utils as utils

class ReplicationManager:

    def __init__(self, identifier, port, verbose=True):
        self._stdout = sys.stdout
        if not verbose:
            dev_null = open(os.devnull, 'w')
            self._stdout = dev_null

        # rm info
        self._identifier = identifier
        self._hostport = socket.gethostname() + ':' + str(port)

        # bind socket
        sock = socket.socket()
        sock.bind(utils.address(self._hostport))
        self._sock = sock

        # membership
        self._members = []

        # rm process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'RM {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _handle_gfd(self, conn, gfd_identifier):
        self._print(f'Connection from GFD {gfd_identifier}')

        identifier, _, message, _ = utils.recv(conn)
        while message is not None:
            if message == 'add':
                self._members.append(identifier)
                self._print(f'Added member {identifier}')
                self._print(f'Current members: {self._members}')
            elif message == 'remove':
                self._members.remove(identifier)
                self._print(f'Removed member {identifier}')
                self._print(f'Current members: {self._members}')
            identifier, _, message, _ = utils.recv(conn)

        self._print(f'Connection closed by GFD {gfd_identifier}')
        for member in self._members:
            self._members.remove(member)
            self._print(f'Removed member {member}')
        self._print(f'Current members: {self._members}')


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()

        while True:
            conn, _ = self._sock.accept()
            identifier, number, data, _ = utils.recv(conn)
            utils.send(conn, self._identifier, number, 'rm')
            # check for gfd
            if data == 'gfd':
                Thread(target=self._handle_gfd, args=[conn, identifier]).start()


    def start(self):
        self._process = Process(target=self._listen)
        self._process.start()


    def stop(self):
        self._print('Stopping RM')
        if self._process is not None:
            self._process.terminate()
            self._sock.shutdown(socket.SHUT_RDWR)


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport
