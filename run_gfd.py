#!/usr/bin/python3

import sys
import signal

import argparse

from components.global_fault_detector import GlobalFaultDetector


gfd = None


def stop(sig, frame):
    if gfd is not None:
        gfd.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='GFD identifier')
    parser.add_argument('-p', '--port', help='GFD TCP port')
    parser.add_argument('-hp', '--hostport', help='RM hostport')

    args = parser.parse_args()

    required = [args.identifier, args.port, args.hostport]
    if any(arg is None for arg in required):
        print('Missing required arg(s)')
        sys.exit(1)

    gfd = GlobalFaultDetector(args.identifier, int(args.port), args.hostport)
    gfd.start()

    signal.signal(signal.SIGINT, stop)
