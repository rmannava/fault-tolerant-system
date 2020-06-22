#!/usr/bin/python3

import sys
import signal

import argparse

from components.local_fault_detector import LocalFaultDetector


def stop(sig, frame):
    if lfd is not None:
        lfd.stop()

if __name__ == '__main__':
    lfd = None

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='LFD identifier')
    parser.add_argument('-hp', '--hostport', help='server hostport')
    parser.add_argument('-int', '--interval', help='heartbeat interval in seconds')

    args = parser.parse_args()

    if args.identifier is None or args.hostport is None or args.interval is None:
        print('Identifier, port, and interval must be specified')
        sys.exit(1)

    lfd = LocalFaultDetector(args.identifier, args.hostport, int(args.interval))
    lfd.start()

    signal.signal(signal.SIGINT, stop)
