#!/usr/bin/python3

import sys
import signal

import argparse

from components.replication_manager import ReplicationManager


rm = None


def stop(sig, frame):
    if rm is not None:
        rm.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='RM identifier')
    parser.add_argument('-p', '--port', help='RM TCP port')

    args = parser.parse_args()

    required = [args.identifier, args.port]
    if any(arg is None for arg in required):
        print('Missing required arg(s)')
        sys.exit(1)

    rm = ReplicationManager(args.identifier, int(args.port))
    rm.start()

    signal.signal(signal.SIGINT, stop)
