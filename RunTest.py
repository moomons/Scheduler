#!/usr/bin/env python

"""

  Flow Parameters

  Traffic generator: D-ITG. Run ITGRecv and ITGLog first on all machines.

  For every SRC to every DST, generate Poisson:
  SRC to DST,
  1x High Bandwidth flow: 600 Mbps, min 300 Mbps
  50x Low Latency flow: 7 Mbps, max delay 1 ms

"""
from collections import defaultdict
from pycon_cfg import *
import os
from enum import Enum
from pycon_def import GetPathList, Mat_BW_Cap, Mat_SWHosts


class FlowType(Enum):
    HighBandwidth = 1
    LowLatency = 2

Duration = 30  # in seconds

List_SRC_DST_Group = [
    ["10.0.0.201", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.211", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.212", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.213", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
]

# Small scale test.
List_SRC_DST_Group = [
    ["10.0.0.201", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
    ["10.0.0.211", ["10.0.0.201", "10.0.0.211", "10.0.0.212", "10.0.0.213"]],
]

Flow_To_Generate_Per_SRCDSTPair = [
    # Count, [FlowType, weight(alpha/beta), Bandwidth(Mbps), MinBandwidth(Mbps), Delay(us)]
    [1, [FlowType.LowLatency, 0.1, 8, 0, 1000]],  # MARK: Set to 80
    # [1, [FlowType.LowLatency, 0.3, 8, 0, 1000]],
    # [1, [FlowType.LowLatency, 0.2, 8, 0, 1000]],
    [1, [FlowType.HighBandwidth, 0.35, 80, 4, 0]],
]

# Small scale test.
# Flow_To_Generate_Per_SRCDSTPair = [
#     [1, [FlowType.LowLatency, 0.1, 8, 0, 1000]],
#     [1, [FlowType.HighBandwidth, 0.5, 500, 300, 0]],
# ]

# DictOfFlows_LowLatency = [{'weight': '1.0', 'srcip': '10.0.0.201', 'dstip': '10.0.0.211', 'bandwidth': 8, 'delay': 1000}]
# DictOfFlows_HighBandwidth = [{'weight': '1.0', 'srcip': '10.0.0.201', 'dstip': '10.0.0.211', 'bandwidth': 500, 'minbandwidth': 250}]
ListOfFlows_LowLatency = []
ListOfFlows_HighBandwidth = []

List_AcceptedFlow_LowLatency = []
List_AcceptedFlow_HighBandwidth = []

# Mat_BW_Cap
Mat_BW_Cap_Original = Mat_BW_Cap
Mat_BW_Cap_Remain = Mat_BW_Cap
Mat_BW_LL_OccupiedBW_Offline = defaultdict(lambda: defaultdict(lambda: 0))
Mat_BW_LL_OccupiedFlowNo_Offline = defaultdict(lambda: defaultdict(lambda: []))


def GenerateAndSortListOfFlows():
    """ Create a complete list of flow commands from the configs. Holy crap """
    global ListOfFlows_LowLatency, ListOfFlows_HighBandwidth

    for OnePair in List_SRC_DST_Group:
        source = OnePair[0]
        dests = OnePair[1]

        for dest in dests:
            if source == dest:
                # logger.info('Skipping same source/dest')
                continue
            logger.info('Source: ' + source + ', Destination: ' + dest)
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
                    # logger.info('Low latency')

                    flowdict['delay'] = delay
                    for i in range(times):
                        ListOfFlows_LowLatency.append(flowdict)  # Add to list

                    # pprint(ListOfFlows_LowLatency)
                elif params[0] == FlowType.HighBandwidth:
                    minbandwidth = params[3]
                    # logger.info('High Bandwidth')

                    flowdict['minbandwidth'] = minbandwidth
                    for i in range(times):
                        ListOfFlows_HighBandwidth.append(flowdict)  # Add to list

                    # pprint(ListOfFlows_HighBandwidth)
                else:
                    logger.error('Undefined type:' + params[0])
                    break

    # Sort the list
    ListOfFlows_LowLatency = list(reversed(sorted(ListOfFlows_LowLatency, key=lambda k: k['weight'])))
    ListOfFlows_HighBandwidth = list(reversed(sorted(ListOfFlows_HighBandwidth, key=lambda k: k['weight'])))


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
            Mat_BW_LL_OccupiedBW_Offline[path[i]][path[i + 1]] += bandwidth
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
    Stat_Accepted_LL = 0
    Stat_Rejected_LL = 0
    for F_LL in ListOfFlows_LowLatency:
        logger.info(dict(F_LL))
        paths, paths_number = GetPathList(F_LL['srcip'], F_LL['dstip'])
        for viable_path in paths:
            bw_rem = GetRemainingBandwidth(viable_path)  # Note: delay in us, bw_rem in Mbps
            delay = GetPathDelay(viable_path)
            if F_LL['bandwidth'] <= bw_rem and delay <= F_LL['delay'] and CheckUpdatedDelay(F_LL):
                # Basic req okay. Check other LL flow delay req.
                F_LL['path'] = viable_path
                F_LL['actual_bandwidth'] = F_LL['bandwidth']
                AddFlow(F_LL, True)
                Stat_Accepted_LL += 1
                break
            path_index = paths.index(viable_path)
            if path_index >= len(paths) - 1:  # didn't find a good path
                logger.warning("Rejected")
                Stat_Rejected_LL += 1

    Stat_Accepted_HB = 0
    Stat_Accepted_HB_UsingWaitList = 0
    Stat_Rejected_HB = 0
    for F_HB in ListOfFlows_HighBandwidth:
        List_WaitingList = []
        logger.info(dict(F_HB))
        paths, paths_number = GetPathList(F_HB['srcip'], F_HB['dstip'])
        for viable_path in paths:
            bw_rem = GetRemainingBandwidth(viable_path)  # Note: delay in us, bw_rem in Mbps
            if F_HB['bandwidth'] <= bw_rem:
                F_HB['path'] = viable_path
                F_HB['actual_bandwidth'] = F_HB['bandwidth']
                AddFlow(F_HB, False)  # Add high bw flow to the list
                Stat_Accepted_HB += 1
                break
            elif bw_rem > F_HB['minbandwidth']:  # Hmm.. Not the best one. Dump it to the waiting list anyway :P
                F_HB['path'] = viable_path
                F_HB['actual_bandwidth'] = bw_rem
                List_WaitingList.append(F_HB)
            path_index = paths.index(viable_path)
            if path_index >= len(paths) - 1:  # Still haven't found a perfect path
                if len(List_WaitingList) > 0:
                    List_WaitingList = list(reversed(sorted(List_WaitingList, key=lambda k: k['actual_bandwidth'])))
                    F_HB = List_WaitingList[0]  # Select the req with largest actual_bandwidth
                    AddFlow(F_HB, False)
                    Stat_Accepted_HB += 1
                    logger.warning("Accepted from the waiting list")
                    Stat_Accepted_HB_UsingWaitList += 1
                    break
                else:
                    logger.warning("Rejected")
                    Stat_Rejected_HB += 1

    logger.info('Static Algo Result: (haven\'t deployed yet)')
    logger.info('Low latency:\nAccepted = ' + str(Stat_Accepted_LL) +
                ', Rejected = ' + str(Stat_Rejected_LL))
    logger.info('High bandwidth:\nAccepted(Full BW) = ' + str(Stat_Accepted_HB) +
                ', Accepted(Partial BW) = ' + str(Stat_Accepted_HB_UsingWaitList) +
                ', Rejected = ' + str(Stat_Rejected_HB))


def WriteITGConCFG_ForOffline(filename):
    portoffset_ll = 22000
    portoffset_hb = 33000
    # poisson_average_pktps = 1000  # Average 1000 packets/sec, -O 1000
    packet_size = 1000  # in bytes, -c 1024
    send_duration = 15000  # in ms, -t 10000
    configfile = ''
    # Example:
    # Host 192.168.109.201 {
    # -a 10.0.0.211 -T UDP -m RTTM -rp 21301 -O 1000 -c 1024 -t 10000
    # -a 10.0.0.211 -T UDP -m RTTM -rp 21302 -O 1000 -c 1024 -t 10000
    # }

    global List_AcceptedFlow_LowLatency
    if len(List_AcceptedFlow_LowLatency) > 0:
        List_AcceptedFlow_LowLatency = sorted(List_AcceptedFlow_LowLatency, key=lambda k: k['srcip'])
        for i, F in enumerate(List_AcceptedFlow_LowLatency):
            List_AcceptedFlow_LowLatency[i]['assigned_port'] = portoffset_ll + i

    global List_AcceptedFlow_HighBandwidth
    if len(List_AcceptedFlow_HighBandwidth) > 0:
        List_AcceptedFlow_HighBandwidth = sorted(List_AcceptedFlow_HighBandwidth, key=lambda k: k['srcip'])
        for i, F in enumerate(List_AcceptedFlow_HighBandwidth):
            List_AcceptedFlow_HighBandwidth[i]['assigned_port'] = portoffset_hb + i

    listallaccepted = sorted(List_AcceptedFlow_LowLatency + List_AcceptedFlow_HighBandwidth, key=lambda k: k['srcip'])

    if len(listallaccepted) > 0:
        for i, F in enumerate(listallaccepted):
            if i == 0:
                current_srcip = F['srcip']
                configfile += 'Host ' + str(current_srcip) + ' {\n'
            else:
                if current_srcip != F['srcip']:
                    configfile += '}\n\n'
                    current_srcip = F['srcip']
                    configfile += 'Host ' + str(current_srcip) + ' {\n'
            assigned_port = listallaccepted[i]['assigned_port']
            bandwidth_Mbps = F['actual_bandwidth']
            poisson_average_pktps = int(1000000 * bandwidth_Mbps / 8.0 / packet_size)
            configfile += '  -a ' + F['dstip'] + ' -m RTTM -rp ' + str(assigned_port) + \
                          ' -O ' + str(poisson_average_pktps) + ' -c ' + str(packet_size) + \
                          ' -t ' + str(send_duration) + '\n'
        configfile += '}\n\n'

    with open(filename, "w") as text_file:
        text_file.write(configfile)


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
            out = runcommand(cmdline, True)

    # destroy existing qos and queues, then create new qos and queues
    # ovs-vsctl list qos
    # ovs-vsctl --all destroy qos
    # ovs-vsctl list queue
    # ovs-vsctl --all destroy queue
    for switch in portlist:
        switchip = switch[0]
        ports = switch[1]
        cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 --all destroy qos"
        out = runcommand(cmdline, True)
        cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 --all destroy queue"
        out = runcommand(cmdline, True)
        for port in ports:
            # ovs-vsctl --db=tcp:TargetIP:6640 -- set port eth1 qos=@newqos2151 -- \
            # --id=@newqos2151 create qos type=linux-htb queues=2151=@q2151,12=@q2152 -- \
            # --id=@q2151 create queue other-config:priority=1 -- \
            # --id=@q2152 create queue other-config:priority=2
            qosname = "nq_" + port
            queueno = switchip[-3:] + port[-1:]
            queuename = "q_" + port
            queuename_hb = queuename + "_hb"  # 1
            queuename_ll = queuename + "_ll"  # 2
            cmdline = "ovs-vsctl --db=tcp:" + switchip + ":6640 -- set port " + port + " qos=@" + qosname + " -- " \
                "--id=@" + qosname + " create qos type=linux-htb queues=" + queueno + "1=@" + queuename_hb + "," + queueno + "2=@" + queuename_ll + " -- " \
                "--id=@" + queuename_hb + " create queue other-config:priority=1  -- " \
                "--id=@" + queuename_ll + " create queue other-config:priority=2"
            out = runcommand(cmdline, True)

    return True


def addflowentries():
    """ Add entries to the flow table """
    # ovs-ofctl -O OpenFlow13 add-flow tcp:ServerIP:6666 priority=20,udp,nw_dst=DSTHOSTIP,udp_dst=5501,actions=set_queue:2151,output:1
    addflowentry_universal(List_AcceptedFlow_LowLatency, "1")  # Careful! 1 for Low Latency, 2 for high bandwidth
    addflowentry_universal(List_AcceptedFlow_HighBandwidth, "2")


def addflowentry_universal(list, flag_hb_ll):
    global Mat_SWHosts
    ovs_mac_to_manageinterfaceip = {
        "00:00:00:1b:cd:03:04:64": "192.168.109.214",
        "00:00:00:1b:cd:03:05:94": "192.168.109.215",
        "00:00:70:e2:84:05:67:7e": "192.168.109.224",
        "00:00:00:1b:cd:03:16:ac": "192.168.109.225",
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
        logger.info('Add flow entry: ' + str(dict(flow)))
        assigned_port = flow['assigned_port']
        dsthost = flow['dstip']
        path = flow['path']
        assert(len(path) >= 3)
        for i in range(1, len(path) - 1):
            prev_node = path[i - 1]
            current_node = path[i]
            next_node = path[i + 1]
            in_port = Mat_SWHosts[prev_node][current_node][1]
            output_port = Mat_SWHosts[current_node][next_node][0]

            ovsserverip = ovs_mac_to_manageinterfaceip[current_node]
            queueno = ovsserverip[-3:] + ovsswitch_port_eth_map[ovsserverip][output_port][-1:] + flag_hb_ll

            cmdline = "ovs-ofctl -O OpenFlow13 add-flow tcp:" + ovsserverip + ":6666 priority=20,udp,nw_dst=" + dsthost + \
                      ",udp_dst=" + str(assigned_port) + ",in_port=" + str(in_port) + ",actions=set_queue:" + queueno + ",output:" + str(output_port)
            out = runcommand(cmdline, True)

    return


def runcommand(cmdline, suppressMessage=False):
    logger.info("Command line: " + cmdline)
    output = os.popen(cmdline)
    out = output.read()
    if not suppressMessage and len(out) > 0:
        logger.info("Execution result: " + out)

    return out


def CallITGController(filename):
    # Call ITGController, run the test
    out = runcommand("java -jar ~/ITGController/ITGController.jar " + filename)

    # Wait for ITGController quit, show the processed log
    out = runcommand("ITGDec /tmp/ITGSend.log")


def RunOffline():
    """ Entry function to start the Offline algorithm simulation """
    logger.info("Running: Offline (Full)")

    # Generate ListOfFlows
    GenerateAndSortListOfFlows()

    # The static algorithm
    OfflineAlgo()

    # Gen ITGController config-file
    WriteITGConCFG_ForOffline("configOffline")

    # ovs-vsctl add qos and queue
    createqueue()

    # ovs-ofctl add output
    addflowentries()

    # TODO: 213: ITGLog. All: ITGRecv, ITGSend -Q -L 192.168.109.213
    # Note: restart the ITGSend to clear the log.

    # Call ITGController and show the result
    CallITGController("configOffline")



def RunPlain():
    """ Entry function to start the plain run(with no algo) """
    logger.info("Running: Plain")

    # Generate ListOfFlows
    GenerateAndSortListOfFlows()

    # Copy the list to the accepted list
    global List_AcceptedFlow_LowLatency, List_AcceptedFlow_HighBandwidth
    List_AcceptedFlow_LowLatency = ListOfFlows_LowLatency
    List_AcceptedFlow_HighBandwidth = ListOfFlows_HighBandwidth

    # Gen ITGController config-file
    WriteITGConCFG_ForOffline("configPlain")

    # Call ITGController and show the result
    CallITGController("configPlain")


def RunDelayAndBandwidthOnly():
    logger.info("Running: Offline (Delay and bandwidth scheduled, will reject flow)")


def RunQueueOnly():
    logger.info("Running: Offline (Only queue, will accept all flows)")


def main():
    logger.info("Choose algo: 1) Plain  2) Offline (Full)  3) Delay and BW  4) Queue only")
    choice = raw_input().lower()
    if choice == "1":
        RunPlain()
    elif choice == "2":
        RunOffline()
    elif choice == "3":
        RunDelayAndBandwidthOnly()
    elif choice == "4":
        RunQueueOnly()
    else:
        print("Invalid input")


if __name__ == '__main__':
    main()

