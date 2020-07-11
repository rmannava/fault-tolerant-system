#!/usr/bin/python3

import sys
import signal

import argparse

from components.server import Server


def stop(sig, frame):
    if server is not None:
        server.stop()


if __name__ == '__main__':
    server = None

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='server identifier')
    parser.add_argument('-p', '--port', help='server TCP port')
    parser.add_argument('-php', '--primary_hostport', help='primary server hostport')
    parser.add_argument('-bhp', '--backup_hostports', help='backup server hostports separated by a space')
    parser.add_argument('-int', '--interval', help='checkpoint interval in seconds')

    args = parser.parse_args()

    if args.identifier is None or args.port is None:
        print('Both identifier and port must be specified')
        sys.exit(1)

    if args.backup_hostports is not None:
        args.backup_hostports = args.backup_hostports.split(' ')
    if args.interval is not None:
        args.interval = int(args.interval)

    server = Server(args.identifier, int(args.port), args.primary_hostport, args.backup_hostports, args.interval)
    server.start()

    signal.signal(signal.SIGINT, stop)
