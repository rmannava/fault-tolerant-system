#!/usr/bin/python3

import sys
import signal

import argparse

from components.local_fault_detector import LocalFaultDetector


lfd = None


def stop(sig, frame):
    if lfd is not None:
        lfd.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--identifier', help='LFD identifier')
    parser.add_argument('-shp', '--server_hostport', help='server hostport')
    parser.add_argument('-ghp', '--gfd_hostport', help='GFD hostport')
    parser.add_argument('-int', '--interval', help='heartbeat interval in seconds')

    args = parser.parse_args()

    required = [args.identifier, args.server_hostport, args.gfd_hostport, args.interval]
    if any(arg is None for arg in required):
        print('Missing required arg(s)')
        sys.exit(1)

    lfd = LocalFaultDetector(args.identifier, args.server_hostport, args.gfd_hostport, int(args.interval))
    lfd.start()

    signal.signal(signal.SIGINT, stop)
