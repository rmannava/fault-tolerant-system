#!/usr/bin/python3

import sys

import argparse

from components.server import Server

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='server identifier')
    parser.add_argument('-p', '--port', help='server TCP port')

    args = parser.parse_args()

    if args.identifier is None or args.port is None:
        print('Both identifier and port must be specified')
        sys.exit(1)

    server = Server(args.identifier, int(args.port), True)
    server.start()
