#!/usr/bin/env python3

import config
import time
import json
import os
import argparse
import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html

GPIO = config.ir_receiver_gpio
GLITCH = 100
PRE_MS = 200

# default: 15
POST_MS = 130
FREQ = 38.0
SHORT = 10
GAP_MS = 100
TOLERANCE = 15

POST_US = POST_MS * 1000
PRE_US = PRE_MS * 1000
GAP_S = GAP_MS / 1000.0
TOLER_MIN = (100 - TOLERANCE) / 100.0
TOLER_MAX = (100 + TOLERANCE) / 100.0

last_tick = 0
in_code = False
code = []
fetching_code = False

pi = None


def normalise(c):
    entries = len(c)
    p = [0]*entries  # Set all entries not processed.
    for i in range(entries):
        if not p[i]:  # Not processed?
            v = c[i]
            tot = v
            similar = 1.0

            # Find all pulses with similar lengths to the start pulse.
            for j in range(i+2, entries, 2):
                if not p[j]:  # Unprocessed.
                    if (c[j]*TOLER_MIN) < v < (c[j]*TOLER_MAX):  # Similar.
                        tot = tot + c[j]
                        similar += 1.0

            # Calculate the average pulse length.
            newv = round(tot / similar, 2)
            c[i] = newv

            # Set all similar pulses to the average value.
            for j in range(i+2, entries, 2):
                if not p[j]:  # Unprocessed.
                    if (c[j]*TOLER_MIN) < v < (c[j]*TOLER_MAX):  # Similar.
                        c[j] = newv
                        p[j] = 1


def tidy_mark_space(record, base):
    ms = {}
    # Find all the unique marks (base=0) or spaces (base=1)
    # and count the number of times they appear,
    rl = len(record)
    for i in range(base, rl, 2):
        if record[i] in ms:
            ms[record[i]] += 1
        else:
            ms[record[i]] = 1

    v = None
    for plen in sorted(ms):
        if v is None:
            e = [plen]
            v = plen
            tot = plen * ms[plen]
            similar = ms[plen]

        elif plen < (v*TOLER_MAX):
            e.append(plen)
            tot += (plen * ms[plen])
            similar += ms[plen]

        else:
            v = int(round(tot/float(similar)))
            # set all previous to v
            for i in e:
                ms[i] = v
            e = [plen]
            v = plen
            tot = plen * ms[plen]
            similar = ms[plen]

    v = int(round(tot/float(similar)))
    # set all previous to v
    for i in e:
        ms[i] = v

    rl = len(record)
    for i in range(base, rl, 2):
        record[i] = ms[record[i]]


def tidy(record):
    tidy_mark_space(record, 0)  # Marks.
    tidy_mark_space(record, 1)  # Spaces.


def end_of_code():
    global code, fetching_code
    if len(code) > SHORT:
        normalise(code)
        fetching_code = False
    else:
        code = []
        print("Short code, probably a repeat, try again")


def cbf(gpio, level, tick):
    global last_tick, in_code, code, fetching_code

    if level != pigpio.TIMEOUT:
        edge = pigpio.tickDiff(last_tick, tick)
        last_tick = tick

        if fetching_code:
            if (edge > PRE_US) and (not in_code):  # Start of a code.
                in_code = True
                pi.set_watchdog(GPIO, POST_MS)  # Start watchdog.

            elif (edge > POST_US) and in_code:  # End of a code.
                in_code = False
                pi.set_watchdog(GPIO, 0)  # Cancel watchdog.
                end_of_code()

            elif in_code:
                code.append(edge)

    else:
        pi.set_watchdog(GPIO, 0)  # Cancel watchdog.
        if in_code:
            in_code = False
            end_of_code()


def rec():
    global pi, last_tick, in_code, code, fetching_code
    pi = pigpio.pi()  # Connect to Pi.
    if not pi.connected:
        print("ERR: pigpiod not started.")
        return

    last_tick = 0
    in_code = False
    code = []
    fetching_code = False

    pi.set_mode(GPIO, pigpio.INPUT)  # IR RX connected to this GPIO.
    pi.set_glitch_filter(GPIO, GLITCH)  # Ignore glitches.
    cb = pi.callback(GPIO, pigpio.EITHER_EDGE, cbf)

    print("Recording")
    code = []
    fetching_code = True
    while fetching_code:
        time.sleep(0.1)

    res = code[:]

    pi.set_glitch_filter(GPIO, 0)  # Cancel glitch filter.
    pi.set_watchdog(GPIO, 0)  # Cancel watchdog.

    tidy(res)
    cb.cancel()
    pi.stop()
    return res
