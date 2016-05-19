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
from collections import defaultdict
from pycon_cfg import *
import os
from pprint import pprint
from enum import Enum
from pycon_def import GetPathList
from pycon_def import Mat_BW_Cap, Mat_BW_Cap_MASK


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
    # Count, [FlowType, weight(alpha/beta), Bandwidth(Mbps), MinBandwidth(Mbps), Delay(us)]
    [2, [FlowType.LowLatency, 0.1, 8, 0, 1000]],  # MARK: Set to 80
    [1, [FlowType.HighBandwidth, 0.1, 500, 300, 0]],
]

# DictOfFlows_LowLatency = [{'weight': '1.0', 'srcip': '10.0.0.201', 'dstip': '10.0.0.211', 'bandwidth': 8, 'delay': 1000}]
# DictOfFlows_HighBandwidth = [{'weight': '1.0', 'srcip': '10.0.0.201', 'dstip': '10.0.0.211', 'bandwidth': 500, 'minbandwidth': 250}]
ListOfFlows_LowLatency = []
ListOfFlows_HighBandwidth = []

# Mat_BW_Cap
Mat_BW_Cap_Original = Mat_BW_Cap
Mat_BW_Cap_Remain = Mat_BW_Cap
# Mat_Link_Share = Mat_BW_Cap
Mat_BW_LL_OccupiedBW_Offline = defaultdict(lambda: defaultdict(lambda: 0))
Mat_BW_LL_OccupiedFlowNo_Offline = defaultdict(lambda: defaultdict(lambda: []))

List_AcceptedFlow_LowLatency = []
List_AcceptedFlow_HighBandwidth = []


def GenerateAndSortListOfFlows():
    """ Create a complete list of flow commands from the configs. Holy crap """
    global ListOfFlows_LowLatency, ListOfFlows_HighBandwidth

    for OnePair in List_SRC_DST_Group:
        source = OnePair[0]
        dests = OnePair[1]

        for dest in dests:
            logger.info('Source: ' + source + ', Destination: ' + dest)
            if source == dest:
                logger.info('Skipping same source/dest')
                continue
            for flow in Flow_To_Generate_Per_SRCDSTPair:
                times = flow[0]
                params = flow[1]
                weight = params[1]
                bandwidth = params[2]

                flowdict = defaultdict(lambda: None)
                flowdict['weight'] = weight
                flowdict['srcip'] = source
                flowdict['dstip'] = dest
                flowdict['bandwidth'] = bandwidth

                if params[0] == FlowType.LowLatency:
                    delay = params[4]
                    logger.info('Low latency')

                    flowdict['delay'] = delay
                    for i in range(times):
                        ListOfFlows_LowLatency.append(flowdict)  # Add to list

                    # pprint(ListOfFlows_LowLatency)
                elif params[0] == FlowType.HighBandwidth:
                    minbandwidth = params[3]
                    logger.info('High Bandwidth')

                    flowdict['minbandwidth'] = minbandwidth
                    for i in range(times):
                        ListOfFlows_HighBandwidth.append(flowdict)  # Add to list

                    # pprint(ListOfFlows_HighBandwidth)
                else:
                    logger.error('Undefined type:' + params[0])
                    break
            # break

        # break


    # Sort the list
    ListOfFlows_LowLatency = sorted(ListOfFlows_LowLatency, key=lambda k: k['weight'], reversed=True)
    ListOfFlows_HighBandwidth = sorted(ListOfFlows_HighBandwidth, key=lambda k: k['weight'], reversed=True)


def GetPathDelay(path, bwoffset=0):
    """ Get the delay from M/M/1 formula for the path (Designed for Low Latency Flows) """
    assert(len(path) >= 3)
    pathdelay = 0.0
    for i in range(1, len(path) - 1):
        linkdelay = 1.0 / (Mat_BW_Cap_Original[path[i]][path[i + 1]] - Mat_BW_LL_OccupiedBW_Offline[path[i]][path[i + 1]] - bwoffset)
        pathdelay += linkdelay

    return pathdelay


def GetRemainingBandwidthAndDelay(path, calculate_delay=False):
    """ Offline algo function. Online algo should directly use Floodlight output(theoretically) """
    assert(len(path) >= 3)
    bottleneckbandwidth = Mat_BW_Cap_Remain[path[0]][path[1]]
    for i in range(1, len(path) - 1):
        rembandwidthonthispath = Mat_BW_Cap_Remain[path[i]][path[i + 1]]
        if rembandwidthonthispath < bottleneckbandwidth:
            bottleneckbandwidth = rembandwidthonthispath

    delay = 0.0
    if calculate_delay:
        delay = GetPathDelay(path)

    return bottleneckbandwidth, delay


def CheckUpdatedDelay(F_LL):
    assert(F_LL['delay'] is not None)
    bwoffset = F_LL['bandwidth']
    for acceptedll in List_AcceptedFlow_LowLatency:
        if GetPathDelay(acceptedll['path'], bwoffset) > acceptedll['delay']:
            # if any existing LL flow's delay would exceed, we can't deploy the new flow! Erh
            return False

    return True


def AddFlow(flow, IsLowLatencyFlow=False):
    assert(flow['path'] is not None)
    path = flow['path']
    bandwidth = flow['actual_bandwidth']
    assert(bandwidth is not None)

    if IsLowLatencyFlow:  # LowLatency Flow
        idx = len(List_AcceptedFlow_LowLatency)
        List_AcceptedFlow_LowLatency.append(flow)  # Add the flow to the accepted list, congrats!
        for i in range(0, len(path) - 1):
            Mat_BW_LL_OccupiedFlowNo_Offline[path[i]][path[i + 1]].append(idx)  # Add to the LL share link
            Mat_BW_LL_OccupiedFlowNo_Offline[path[i]][path[i + 1]] += bandwidth
            Mat_BW_Cap_Remain[path[i]][path[i + 1]] -= bandwidth
            assert(Mat_BW_Cap_Remain[path[i]][path[i + 1]] >= 0)
    else:                 # HighBandwidth Flow
        idx = len(List_AcceptedFlow_HighBandwidth)
        List_AcceptedFlow_HighBandwidth.append(flow)  # Add the flow to the accepted list, congrats!
        for i in range(0, len(path) - 1):
            Mat_BW_Cap_Remain[path[i]][path[i + 1]] -= bandwidth  # Occupy the bandwidth
            assert(Mat_BW_Cap_Remain[path[i]][path[i + 1]] >= 0)  # Of course the bandwidth shouldn't be minus


def RunStatic():
    """ Entry function to start the static algorithm simulation """

    # TODO: Run ITGLog on 213. Run ITGRecv, ITGSend -Q -L 192.168.109.213 on all

    # TODO: Gen config list for ITGController from List_SRC_DST and Flow_To_Generate_Per_SRCDSTPair
    # MARK: Debugging, just use first pair in List_SRC_DST

    # Generate ListOfFlows
    global ListOfFlows_LowLatency, ListOfFlows_HighBandwidth
    GenerateAndSortListOfFlows()

    # The static algorithm
    logger.info('Static Algorithm starting')
    # Statistics info to
    Stat_Accepted = 0
    Stat_Rejected = 0

    for F_LL in ListOfFlows_LowLatency:
        logger.info(F_LL)
        paths, paths_number = GetPathList(F_LL['srcip'], F_LL['dstip'])
        for viable_path in paths:
            bw_rem, delay = GetRemainingBandwidthAndDelay(viable_path, True)  # Note: delay in us, bw_rem in Mbps
            if F_LL['bandwidth'] <= bw_rem and delay <= F_LL['delay'] and CheckUpdatedDelay(F_LL):
                # Basic req okay. Check other LL flow delay req.
                F_LL['path'] = viable_path
                F_LL['actual_bandwidth'] = F_LL['bandwidth']
                AddFlow(F_LL, True)
                break

    for F_HB in ListOfFlows_HighBandwidth:
        List_WaitingList = []
        logger.info(F_HB)

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

