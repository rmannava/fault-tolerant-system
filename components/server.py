""" A server in a distributed system. """

import os
import sys
import time
import socket
from multiprocessing import Process
from threading import Thread

from components.server_state import ServerState
import components.utils as utils

class Server:
    """ The Server class.

    Communicates via a TCP socket.
    """

    def __init__(self, identifier, port, primary=None, backups=None,
                 interval=None, verbose=True):
        """ Creates a Server object.

        Binds the specified port, and opens a connection to each backup.

        Providing primary sets the server as a backup, while providing backups
        sets the server as the primary. Providing neither defaults to active
        replication.

        If backups is provided, interval must also be provided.

        Args:
            identifier: The int or string used to identify this server.
            port: The int TCP port number this server should listen on.
            primary: A single string hostport of the primary server that this
                server is a backup for. Can be None if the server is not a
                backup.
            backups: A single string or list of string hostports of
                the backup servers that this server is the primary for. Can be
                None if the server is not the primary.
            interval: The positive integer interval in seconds at which the
                server should send checkpoints to the backups. Can be None if
                the server is not the primary.
            verbose: A boolean; if True the server will print info to stdout.
        """
        # validate arguments
        if not isinstance(identifier, str) and not isinstance(identifier, int):
            raise TypeError(f'identifier {identifier} has type '
                            f'{type(identifier)}; must be int or str')
        if not isinstance(port, int):
            raise TypeError(f'port {port} has type {type(port)}; must be int')
        if primary is not None and backups is not None:
            raise ValueError('both primary and backups cannot be provided')
        if primary is not None:
            if not isinstance(primary, str):
                raise TypeError(f'primary {primary} has type {type(primary)}; '
                                'must be str')
        if backups is not None:
            if not isinstance(backups, list):
                backups = [backups]
            if not all(isinstance(backup, str) for backup in backups):
                raise TypeError('backups must have type str or list[str]')
            if interval is None:
                raise ValueError('backups has been provided; interval must '
                                 'also be provided')
        if interval is not None:
            if not isinstance(interval, int):
                raise TypeError(f'interval {interval} has type '
                                f'{type(interval)}; ' 'must be int')
            if interval <= 0:
                raise ValueError(f'interval {interval} must be a positive '
                                 'value')
            if backups is None:
                raise ValueError('interval has been provided; backups must '
                                 'also be provided')
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
        self._primary = primary
        self._backups = backups
        self._interval = interval

        # bind sockets
        sock = socket.socket()
        sock.bind(utils.address(self._hostport))
        self._sock = sock
        self._backup_socks = {}
        if backups is not None:
            for backup in backups:
                sock = socket.socket()
                self._backup_socks[backup] = sock

        # server state
        self._state = ServerState()

        # server process
        self._process = None


    def _print(self, *args, **kwargs):
        comb_args = ' '.join(args)
        print(f'Server {self._identifier}: ' + comb_args, **kwargs,
              file=self._stdout)


    def _handle_lfd(self, conn, lfd_identifier):
        self._print(f'Connection from LFD {lfd_identifier}')

        _, number, heartbeat, _ = utils.recv(conn)
        while heartbeat is not None:
            utils.send(conn, self._identifier, number, heartbeat)
            _, number, heartbeat, _ = utils.recv(conn)

        self._print(f'Connection closed by LFD {lfd_identifier}')


    def _handle_primary(self, conn, primary_identifier):
        self._print(f'Connection from primary Server {primary_identifier}')

        _, number, _, checkpoint = utils.recv(conn)
        while checkpoint is not None:
            self._state = checkpoint
            self._print(f'Received checkpoint (#{number}) {checkpoint}')

            utils.send(conn, self._identifier, number, 'ok')
            _, number, _, checkpoint = utils.recv(conn)

        self._print('Connection closed by primary Server '
                    f'{primary_identifier}')


    def _handle_backups(self):
        backup_identifiers = []
        connected = [False for i in range(len(self._backups))]
        for i in range(len(self._backups)):
            backup = self._backups[i]
            sock = self._backup_socks[backup]
            # connect to backup
            self._print(f'Connecting to backup at {backup}')
            sock.connect(utils.address(backup))

            utils.send(sock, self._identifier, 0, 'primary')
            backup_identifier, _, _, _ = utils.recv(sock)
            # make sure backup is still connected
            if backup_identifier is None:
                sock.close()
                self._backup_socks[backup] = socket.socket()
                self._print(f'Connection closed by backup at {backup}')
            backup_identifiers.append(backup_identifier)
            connected[i] = True
            self._print(f'Connected to backup Server {backup_identifier}')

        number = 1
        while True:
            for i in range(len(self._backups)):
                backup = self._backups[i]
                sock = self._backup_socks[backup]
                backup_identifier = backup_identifiers[i]

                if connected[i]:
                    self._print(f'Sending checkpoint (#{number}) '
                                f'{self._state} to backup Server '
                                f'{backup_identifier}')
                    utils.send(sock, self._identifier, number,
                               state=str(self._state))

                    _, _, res, _ = utils.recv(sock)
                    if res is None:
                        connected[i] = False
                        sock.close()
                        self._backup_socks[backup] = socket.socket()
                        self._print('Connection closed by backup Server '
                                    f'{backup_identifier}')

            number += 1
            time.sleep(self._interval)


    def _handle_client(self, conn, client_identifier):
        self._print(f'Connection from Client {client_identifier}')

        _, number, request, _ = utils.recv(conn)
        while request is not None:
            self._print(f'Received (#{number}) {request} from Client '
                        f'{client_identifier}')

            response = self._state.update(int(request))
            self._print(f'Sending (#{number}) {response} to Client '
                        f'{client_identifier}')
            utils.send(conn, self._identifier, number, response)

            _, number, request, _ = utils.recv(conn)

        self._print(f'Connection closed by Client {client_identifier}')


    def _listen(self):
        self._sock.listen()

        if self.is_primary():
            self._print(f'Starting primary at hostport {self._hostport}')
            Thread(target=self._handle_backups).start()
        else:
            self._print(f'Starting at hostport {self._hostport}')

        while True:
            conn, _ = self._sock.accept()
            identifier, number, data, _ = utils.recv(conn)
            utils.send(conn, self._identifier, number, 'server')
            # check for lfd/client
            if data == 'lfd':
                Thread(target=self._handle_lfd, args=[conn, identifier]).start()
            elif data == 'client':
                Thread(target=self._handle_client,
                       args=[conn, identifier]).start()


    def _wait(self):
        self._print(f'Starting backup at hostport {self._hostport}')
        self._sock.listen()

        while True:
            conn, _ = self._sock.accept()
            identifier, number, data, _ = utils.recv(conn)
            utils.send(conn, self._identifier, number, 'backup')
            # check for lfd/primary
            if data == 'lfd':
                Thread(target=self._handle_lfd, args=[conn, identifier]).start()
            elif data == 'primary':
                Thread(target=self._handle_primary,
                       args=[conn, identifier]).start()


    def start(self):
        if self.is_active() or self.is_primary():
            self._process = Process(target=self._listen)
        else:
            self._process = Process(target=self._wait)
        self._process.start()


    def stop(self):
        self._print('Stopping server')
        if self._process is not None:
            # stop serving requests
            self._process.terminate()

            # stop listening for connections
            self._sock.shutdown(socket.SHUT_RDWR)
            if self.is_primary():
                for backup in self._backups:
                    self._backup_socks[backup].close()
                    self._backup_socks[backup] = socket.socket()


    def is_running(self):
        return self._process.is_alive()


    def hostport(self):
        return self._hostport


    def is_active(self):
        return (self._primary is None and self._backups is None)


    def is_primary(self):
        return self._backups is not None


    def is_backup(self):
        return self._primary is not None
