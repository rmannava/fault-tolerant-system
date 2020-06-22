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

    args = parser.parse_args()

    if args.identifier is None or args.port is None:
        print('Both identifier and port must be specified')
        sys.exit(1)

    server = Server(args.identifier, int(args.port))
    server.start()

    signal.signal(signal.SIGINT, stop)
