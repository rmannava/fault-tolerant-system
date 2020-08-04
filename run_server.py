#!/usr/bin/python3

import sys
import signal

import argparse

from components.server import Server


server = None


def stop(sig, frame):
    if server is not None:
        server.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='server identifier')
    parser.add_argument('-p', '--port', help='server TCP port')
    parser.add_argument('-hp', '--hostports', help='server hostports')
    parser.add_argument('-int', '--interval', help='server interval in seconds')
    parser.add_argument('-a', '--active', default=False, action='store_true', help='active/passive replication')

    args = parser.parse_args()

    required = [args.identifier, args.port, args.hostports, args.interval]
    if any(arg is None for arg in required):
        print('Missing required arg(s)')
        sys.exit(1)

    args.hostports = args.hostports.split(' ')

    server = Server(args.identifier, int(args.port), args.hostports, int(args.interval), args.active)
    server.start()

    signal.signal(signal.SIGINT, stop)
