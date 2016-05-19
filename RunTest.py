#!/usr/bin/env python

"""

  Flow Parameters

  Traffic generator: D-ITG. Run ITGRecv and ITGLog first on all machines.

  For every SRC to every DST, generate Poisson:
  SRC to DST,
  1x High Bandwidth flow: 600 Mbps, min 300 Mbps
  50x Low Latency flow: 7 Mbps, max delay 1 ms

  Online Background flows:
  215->224->214, 215->225->214, 214->224->215, 214->225->215
  1x High Bandwidth flow: 200 Mbps each (fixed)

"""
from pycon_cfg import *
import os
from enum import Enum


class FlowType(Enum):
    HighBandwidth = 1
    LowLatency = 2

Machine_List = [
    "10.0.0.201",
    "10.0.0.211",
    "10.0.0.212",
    "10.0.0.213",
]

Duration = 30  # in seconds

List_SRC_DST_Pair = [
    ["10.0.0.201", "10.0.0.211"],
    ["10.0.0.201", "10.0.0.212"],
    ["10.0.0.201", "10.0.0.213"],
    ["10.0.0.211", "10.0.0.201"],
    ["10.0.0.211", "10.0.0.212"],
    ["10.0.0.211", "10.0.0.213"],
    ["10.0.0.212", "10.0.0.201"],
    ["10.0.0.212", "10.0.0.211"],
    ["10.0.0.212", "10.0.0.213"],
    ["10.0.0.213", "10.0.0.201"],
    ["10.0.0.213", "10.0.0.211"],
    ["10.0.0.213", "10.0.0.212"],
]

List_SRC_DST_Group = [
    ["10.0.0.201", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.211", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.212", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.213", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
]

Flow_To_Generate_Per_SRCDSTPair = [
    # [FlowType, alpha/beta, Bandwidth(Mbps), MinBandwidth(Mbps), Delay(us)]
    [FlowType.LowLatency, 0.1, 8, 0, 1000],
    [FlowType.HighBandwidth, 0.1, 500, 300, 0],
]
FlowCount_LowLatency = 2  # MARK: Set to 80
FlowCount_HighBandwidth = 1


def RunStatic():
    # TODO: Run ITGLog on 213. Run ITGRecv, ITGSend -Q -L 192.168.109.213 on all

    # TODO: Gen config list for ITGController from List_SRC_DST and Flow_To_Generate_Per_SRCDSTPair
    # MARK: Debugging, just use first pair in List_SRC_DST
    for OnePair in List_SRC_DST_Group:
        source = OnePair[0]
        dests = OnePair[1]
        for dest in dests:
            logger.info('Source: ' + source + ', Destination: ' + dest)
            if source == dest:
                logger.info('Skipping same source/dest')
                continue
        break

    # TODO: Gen ITGController config-file

    # TODO: Call ITGController

    # Wait for ITGController quit

    # TODO: Collect result, and process them, show them


def main():
    RunStatic()

if __name__ == '__main__':
    main()

def runcommand(cmdline):
    logger.info("Command line: " + cmdline)
    output = os.popen(cmdline)
    out = output.read()
    if len(out) > 0:
        logger.info("Execution result: " + out)

    return out

