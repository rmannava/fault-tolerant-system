#!/usr/bin/python3

import sys

import argparse

from components.client import Client

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='client identifier')
    parser.add_argument('-hp', '--hostport', help='server hostport')
    parser.add_argument('-int', '--interval', help='client request interval in seconds')
    parser.add_argument('-l', '--limit', help='limit number of client requests')

    args = parser.parse_args()

    if args.identifier is None or args.hostport is None or args.interval is None:
        print('Identifier, port, and interval must be specified')
        sys.exit(1)

    client = Client(args.identifier, args.hostport, int(args.interval), True)
    client.start(args.limit)
