""" A global fault detector in a distributed system. """

import os
import sys
import socket
from multiprocessing import Process
from threading import Thread

import components.utils as utils

class GlobalFaultDetector:
    """ The GlobalFaultDetector class.

    Communicates via a TCP socket.
    """

    def __init__(self, identifier, port, verbose=True):
        """ Creates a GlobalFaultDetector object.

        Binds the specified port.

        Args:
            identifier: The int or string used to identify this GFD.
            port: The int TCP port number this server should listen on.
            verbose: A boolean; if True the GFD will print info to stdout.
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

        # gfd info
        self._identifier = identifier
        self._hostport = socket.gethostname() + ':' + str(port)

        # bind socket
        sock = socket.socket()
        sock.bind(utils.address(self._hostport))
        self._sock = sock

        # membership
        self._members = []

        # gfd process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'GFD {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _handle_lfd(self, conn, lfd_identifier):
        self._print(f'Connection from LFD {lfd_identifier}')

        _, _, message, _ = utils.recv(conn)
        while message is not None:
            if message == 'add':
                self._members.append(lfd_identifier)
                self._print(f'Added member {lfd_identifier}')
                self._print(f'Current members: {self._members}')
            elif message == 'remove':
                self._members.remove(lfd_identifier)
                self._print(f'Removed member {lfd_identifier}')
                self._print(f'Current members: {self._members}')
            _, _, message, _ = utils.recv(conn)

        self._print(f'Connection closed by LFD {lfd_identifier}')
        if lfd_identifier in self._members:
            self._members.remove(lfd_identifier)
            self._print(f'Removed member {lfd_identifier}')
            self._print(f'Current members: {self._members}')


    def _listen(self):
        self._print(f'Starting at hostport {self._hostport}')
        self._sock.listen()

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
