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
from pycon_def import Mat_BW_Cap, Mat_SWHosts


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

    return pathdelay  # Note: Should already be in us because the BW is in Mbps


def GetRemainingBandwidth(path):
    """ Offline algo function. Online algo should directly use Floodlight output(theoretically) """
    assert(len(path) >= 3)
    bottleneckbandwidth = Mat_BW_Cap_Remain[path[0]][path[1]]
    for i in range(1, len(path) - 1):
        rembandwidthonthispath = Mat_BW_Cap_Remain[path[i]][path[i + 1]]
        if rembandwidthonthispath < bottleneckbandwidth:
            bottleneckbandwidth = rembandwidthonthispath

    return bottleneckbandwidth


def CheckUpdatedDelay(F_LL):
    """ Check if any existing LL flow delay will become unacceptable after new LL flow joins """
    assert(F_LL['delay'] is not None)
    bwoffset = F_LL['bandwidth']
    for acceptedll in List_AcceptedFlow_LowLatency:
        if GetPathDelay(acceptedll['path'], bwoffset) > acceptedll['delay']:
            # if any existing LL flow's delay would exceed, we can't deploy the new flow! Erh
            return False

    return True


def AddFlow(flow, IsLowLatencyFlow=False):
    """ Let's Rock """
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


def OfflineAlgo():
    logger.info('Static Algorithm starting')
    # Statistics info to collect & show
    Stat_Accepted = 0
    Stat_Accepted_FromWaitList = 0
    Stat_Rejected = 0

    for F_LL in ListOfFlows_LowLatency:
        logger.info(F_LL)
        paths, paths_number = GetPathList(F_LL['srcip'], F_LL['dstip'])
        for i, viable_path in paths:
            bw_rem = GetRemainingBandwidth(viable_path)  # Note: delay in us, bw_rem in Mbps
            delay = GetPathDelay(viable_path)
            if F_LL['bandwidth'] <= bw_rem and delay <= F_LL['delay'] and CheckUpdatedDelay(F_LL):
                # Basic req okay. Check other LL flow delay req.
                F_LL['path'] = viable_path
                F_LL['actual_bandwidth'] = F_LL['bandwidth']
                AddFlow(F_LL, True)
                Stat_Accepted += 1
                break
            if i >= len(paths) - 1:  # didn't find a good path
                Stat_Rejected += 1

    for F_HB in ListOfFlows_HighBandwidth:
        List_WaitingList = []
        logger.info(F_HB)
        paths, paths_number = GetPathList(F_HB['srcip'], F_HB['dstip'])
        for i, viable_path in paths:
            bw_rem = GetRemainingBandwidth(viable_path)  # Note: delay in us, bw_rem in Mbps
            if F_HB['bandwidth'] <= bw_rem:
                F_HB['path'] = viable_path
                F_HB['actual_bandwidth'] = F_HB['bandwidth']
                AddFlow(F_HB, False)  # Add high bw flow to the list
                Stat_Accepted += 1
                break
            elif bw_rem > 0:  # Hmm.. Not the best one. Dump it to the waiting list anyway :P
                F_HB['path'] = viable_path
                F_HB['actual_bandwidth'] = bw_rem
                List_WaitingList.append(F_HB)
            if i >= len(paths) - 1:  # Still haven't found a perfect path
                if len(List_WaitingList) > 0:
                    List_WaitingList = sorted(List_WaitingList, key=lambda k: k['actual_bandwidth'], reversed=True)
                    F_HB = List_WaitingList[0]  # Select the req with largest actual_bandwidth
                    AddFlow(F_HB, False)
                    Stat_Accepted += 1
                    Stat_Accepted_FromWaitList += 1
                    break
                else:
                    Stat_Rejected += 1

    logger.info('Static Algo Result: (haven\'t deployed yet)')
    logger.info('Stat_Accepted = ' + Stat_Accepted +
                ', Stat_Accepted_FromWaitList = ' + Stat_Accepted_FromWaitList +
                ', Stat_Rejected = ' + Stat_Rejected)


def RunOffline():
    """ Entry function to start the Offline algorithm simulation """

    # TODO: Run ITGLog on 213. Run ITGRecv, ITGSend -Q -L 192.168.109.213 on all

    # Generate ListOfFlows
    global ListOfFlows_LowLatency, ListOfFlows_HighBandwidth
    GenerateAndSortListOfFlows()

    # The static algorithm
    OfflineAlgo()

    # Gen ITGController config-file
    portoffset_ll = 22000
    portoffset_hb = 33000
    # poisson_average_pktps = 1000  # Average 1000 packets/sec, -O 1000
    packet_size = 1000  # in bytes, -c 1024
    send_duration = 10000  # in ms, -t 10000
    configfile = ''
    # Example:
    # Host 192.168.109.201 {
    # -a 10.0.0.211 -T UDP -m RTTM -rp 21301 -O 1000 -c 1024 -t 10000
    # -a 10.0.0.211 -T UDP -m RTTM -rp 21302 -O 1000 -c 1024 -t 10000
    # }

    global List_AcceptedFlow_LowLatency
    listsorted_LL = sorted(List_AcceptedFlow_LowLatency, key=lambda k: k['srcip'])
    for i, F in listsorted_LL:  # weaving the config content. Looks dirty, but should work ;)
        if i == 0:
            current_srcip = F['srcip']
            configfile += 'Host ' + str(current_srcip) + ' {\n'
        else:
            if current_srcip != F['srcip']:
                configfile += '}\n\n'
                current_srcip = F['srcip']
                configfile += 'Host ' + str(current_srcip) + ' {\n'
            assigned_port = portoffset_ll + i
            bandwidth_Mbps = F['actual_bandwidth']
            poisson_average_pktps = 1000000 * bandwidth_Mbps / 8.0 / packet_size
            listsorted_LL[i]['assigned_port'] = assigned_port
            configfile += '  -a ' + F['dstip'] + ' -T UDP -m RTTM -rp ' + str(assigned_port) + \
                          ' -O ' + str(poisson_average_pktps) + ' -c ' + str(packet_size) + \
                          ' -t ' + str(send_duration) + '\n'
    configfile += '}\n\n'
    List_AcceptedFlow_LowLatency = listsorted_LL

    global List_AcceptedFlow_HighBandwidth
    listsorted_HB = sorted(List_AcceptedFlow_HighBandwidth, key=lambda k: k['srcip'])
    for i, F in listsorted_HB:
        if i == 0:
            current_srcip = F['srcip']
            configfile += 'Host ' + str(current_srcip) + ' {\n'
        else:
            if current_srcip != F['srcip']:
                configfile += '}\n\n'
                current_srcip = F['srcip']
                configfile += 'Host ' + str(current_srcip) + ' {\n'
            assigned_port = portoffset_hb + i
            bandwidth_Mbps = F['actual_bandwidth']
            poisson_average_pktps = 1000000 * bandwidth_Mbps / 8.0 / packet_size
            listsorted_HB[i]['assigned_port'] = assigned_port
            configfile += '  -a ' + F['dstip'] + ' -T UDP -m RTTM -rp ' + str(assigned_port) + \
                          ' -O ' + str(poisson_average_pktps) + ' -c ' + str(packet_size) + \
                          ' -t ' + str(send_duration) + '\n'
    configfile += '}\n\n'
    List_AcceptedFlow_HighBandwidth = listsorted_HB

    with open("configStatic", "w") as text_file:
        text_file.write(configfile)

    # TODO: ovs-vsctl add qos and queue
    createqueue()

    # TODO: ovs-ofctl add output
    addflowentries()

    # Call ITGController
    out = runcommand("~/ITGController/ITGController configStatic")

    # Wait for ITGController quit

    # TODO: Collect result, and process them, show them
    out = runcommand("ITGDec X.log")


def createqueue():
    portlist = [
        ["192.168.109.214", ["eth1", "eth2", "eth3", "eth4"]],
        ["192.168.109.215", ["eth1", "eth2", "eth3", "eth4"]],
        ["192.168.109.224", ["eth1", "eth2"]],
        ["192.168.109.225", ["eth1", "eth2"]],
    ]

    # Clear binded qos from ports first
    # ovs-vsctl clear port eth1 qos
    for switch in portlist:
        switchip = switch[0]
        ports = switch[1]
        for port in ports:
            cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 clear port " + port + " qos"
            out = runcommand(cmdline)

    # destroy existing qos and queues, then create new qos and queues
    # ovs-vsctl list qos
    # ovs-vsctl --all destroy qos
    # ovs-vsctl list queue
    # ovs-vsctl --all destroy queue
    for switch in portlist:
        switchip = switch[0]
        ports = switch[1]
        cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 --all destroy qos"
        out = runcommand(cmdline)
        cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 --all destroy queue"
        out = runcommand(cmdline)
        for port in ports:
            # ovs-vsctl --db=tcp:TargetIP:6640 -- set port eth1 qos=@newqos2151 -- \
            # --id=@newqos2151 create qos type=linux-htb queues=2151=@q2151,12=@q2152 -- \
            # --id=@q2151 create queue other-config:priority=1 -- \
            # --id=@q2152 create queue other-config:priority=2
            qosname = "nq_" + port
            queueno = switch[-3:] + port[-1:]
            queuename = "q_" + port
            queuename_hb = queuename + "_hb"  # 1
            queuename_ll = queuename + "_ll"  # 2
            cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 -- set port " + port + " qos=@" + qosname + " -- \
                --id=@" + qosname + " create qos type=linux-htb queues=" + queueno + "1=@" + queuename_hb + "," + queueno + "2=@" + queuename_ll + " -- \
                --id=@" + queuename_hb + " create queue other-config:priority=1 -- \
                --id=@" + queuename_ll + " create queue other-config:priority=2"
            out = runcommand(cmdline)

    return True


def addflowentries():
    """ Add entries to the flow table """
    # ovs-ofctl -O OpenFlow13 add-flow tcp:ServerIP:6666 priority=20,udp,nw_dst=DSTHOSTIP,udp_dst=5501,actions=set_queue:2151,output:1
    addflowentry_universal(List_AcceptedFlow_LowLatency, "2")  # Careful! 2 for Low Latency, 1 for high bandwidth
    addflowentry_universal(List_AcceptedFlow_HighBandwidth, "1")


def addflowentry_universal(list, flag_hb_ll):
    global Mat_SWHosts
    ovs_mac_to_manageinterfaceip = {
        "00:1b:cd:03:04:64": "192.168.109.214",
        "00:1b:cd:03:05:94": "192.168.109.215",
        "00:1b:cd:03:19:90": "192.168.109.224",
        "00:1b:cd:03:16:ac": "192.168.109.225",
    }
    ovsswitch_port_eth_map = {
        "192.168.109.214": {
            1: "eth1",
            2: "eth2",
            3: "eth3",
            4: "eth4",
        },
        "192.168.109.215": {
            1: "eth1",
            2: "eth2",
            3: "eth3",
            4: "eth4",
        },
        "192.168.109.224": {
            1: "eth1",
            2: "eth2",
        },
        "192.168.109.225": {
            4: "eth1",
            5: "eth2",
        },
    }

    for flow in list:
        logger.info('Add flow entry: ' + flow)
        assigned_port = flow['assigned_port']
        dsthost = flow['dstip']
        path = flow['path']
        assert(len(path) > 3)
        for i in range(1, len(path) - 2):
            prev_node = path[i - 1]
            current_node = path[i]
            next_node = path[i + 1]
            in_port = Mat_SWHosts[prev_node][current_node][1]
            output_port = Mat_SWHosts[current_node][next_node][0]

            ovsserverip = ovs_mac_to_manageinterfaceip[current_node]
            queueno = ovsserverip[-3:] + ovsswitch_port_eth_map[ovsserverip][output_port][-1:] + flag_hb_ll

            cmdline = "ovs-ofctl -O OpenFlow13 add-flow tcp:" + ovsserverip + ":6666 priority=20,udp,nw_dst=" + dsthost + \
                      ",udp_dst=" + str(assigned_port) + ",in_port=" + in_port + ",actions=set_queue:" + queueno + ",output:" + output_port
            out = runcommand(cmdline)


def runcommand(cmdline):
    logger.info("Command line: " + cmdline)
    output = os.popen(cmdline)
    out = output.read()
    if len(out) > 0:
        logger.info("Execution result: " + out)

    return out


def main():
    RunOffline()


if __name__ == '__main__':
    main()

