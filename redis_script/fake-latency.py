#!/usr/bin/python3

import argparse
import subprocess
import signal
import sys
import time

INTERFACE = ""

def unset_lat_delay(iface):
    delay_us = 10
    out = ""
    cmd = ["sudo", "tc", "qdisc", "del", "dev", iface, "root", "netem",
            "delay", str(delay_us) + "us"]

    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if(e.returncode == 2):
            return # There was no rule to begin with
        print("Cannot unset delay: " + str(e))
        print(out)

    return

# Set a latency of delay us on server with interface name iface
def set_lat_delay(iface, delay_us):
    out = ""
    cmd = ["sudo", "tc", "qdisc", "add", "dev", iface, "root", "netem",
            "delay", str(delay_us) + "us"]

    # First unset any existing rule
    unset_lat_delay(iface)

    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        print("Cannot set delay: " + str(e))
        print(out)

    return

def exit_gracefully(arg1, arg2):
    print("Exit signal received, remove latency rule")
    unset_lat_delay(INTERFACE)
    sys.exit()

# Take care of arguments
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--interface", help="interface name", required=True)
parser.add_argument("-r", "--reverse", help="decrease latency starting from the parameter value")
parser.add_argument("-p", "--period", help="update period in seconds", required=True)
parser.add_argument("-l", "--latency", help="us latency to add/remove each period", required=True)
parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
args = parser.parse_args()

LATENCY = 0
if(args.reverse):
    LATENCY = int(args.reverse)
PERIOD = int(args.period)
INTERFACE = args.interface
INCR = int(args.latency)

# Catch signals to exit gracefully
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)

while True:
    if(args.verbose):
        print("Setting latency to " + str(LATENCY))
    set_lat_delay(INTERFACE, LATENCY)
    time.sleep(PERIOD)
    if(args.reverse):
        LATENCY -= INCR
        if(LATENCY < 0):
            LATENCY = 0
    else:
        LATENCY += INCR



