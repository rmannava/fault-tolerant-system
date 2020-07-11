#!/usr/bin/python3

import sys
import signal

import argparse

from components.client import Client


def stop(sig, frame):
    if client is not None:
        client.stop()

if __name__ == '__main__':
    client = None

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='client identifier')
    parser.add_argument('-hp', '--hostports', help='server hostports separated by a space')
    parser.add_argument('-int', '--interval', help='client request interval in seconds')
    parser.add_argument('-l', '--limit', help='limit number of client requests')

    args = parser.parse_args()

    if args.identifier is None or args.hostports is None or args.interval is None:
        print('Identifier, hostports, and interval must be specified')
        sys.exit(1)

    client = Client(args.identifier, args.hostports.split(' '), int(args.interval))
    client.start(args.limit)

    signal.signal(signal.SIGINT, stop)
