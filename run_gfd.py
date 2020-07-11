#!/usr/bin/python3

import sys
import signal

import argparse

from components.global_fault_detector import GlobalFaultDetector


def stop(sig, frame):
    if gfd is not None:
        gfd.stop()


if __name__ == '__main__':
    gfd = None

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='GFD identifier')
    parser.add_argument('-p', '--port', help='GFD TCP port')

    args = parser.parse_args()

    if args.identifier is None or args.port is None:
        print('Both identifier and port must be specified')
        sys.exit(1)

    gfd = GlobalFaultDetector(args.identifier, int(args.port))
    gfd.start()

    signal.signal(signal.SIGINT, stop)
