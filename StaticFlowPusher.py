"""
Reference: http://blog.csdn.net/fei_zodiac/article/details/24706313
"""

import httplib
from pycon_def import *
from pycon_cfg import *
import os


FlowMod_n = 0  # make this variable global


class StaticFlowPusher(object):

    def __init__(self, server):
        self.server = server

    def get(self, data):
        ret = self.rest_call({}, 'GET')
        return json.loads(ret[2])

    def set(self, data):
        ret = self.rest_call(data, 'POST')
        return ret[0] == 200

    def remove(self, objtype, data):
        ret = self.rest_call(data, 'DELETE')
        return ret[0] == 200

    def rest_call(self, data, action):
        path = '/wm/staticflowpusher/json'
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            }
        body = json.dumps(data)
        conn = httplib.HTTPConnection(self.server, 8080)
        conn.request(action, path, body, headers)
        response = conn.getresponse()
        ret = (response.status, response.reason, response.read())
        print ret
        conn.close()

        # TODO: Should log this to file, controlled by a global flag
        return ret


def PushFlowMod(route, att, queue=0, noport=0):
    """ Send Flow Mod Message to switches, one by one """

    global FlowMod_n
    pusher = StaticFlowPusher(Floodlight_IP)  # Controller IP

    for INDEX in range(1, len(route) - 1):
        # print INDEX
        FlowMod_n += 1
        # Setup the Flow Entry for route[INDEX] to route[INDEX+1]
        if INDEX < len(route) - 1:
            flow1 = {
                "name": "pycon-flow-" + str(FlowMod_n),
                "switch": route[INDEX],
                "cookie": "0",
                "priority": "3",
                "active": "true",
                "idle_timeout": "50",  # DEBUG 50. Release 5
                "in_port": str(Mat_SWHosts[route[INDEX - 1]][route[INDEX]][1]),
                "eth_type": "0x0800",  # IPv4
                "ip_proto": "6",  # TCP
                "ipv4_src": att['ip_src'],
                "ipv4_dst": att['ip_dst'],
                # "ip_tos": "1",
            }
            if noport == 0:
                flow1['tcp_src'] = att['tcp_src']
                flow1['tcp_dst'] = att['tcp_dst']
        if queue == 0:
            flow1["actions"] = "output=" + str(Mat_SWHosts[route[INDEX]][route[INDEX + 1]][0])
        elif queue == 1:
            # TODO: Need queuing for SEBF
            # queuenum: 0 for slow, 1 for fast. See def vsctl_remote_db_create() for more info.
            flow1["actions"] = "set_queue=0,output=" + str(Mat_SWHosts[route[INDEX]][route[INDEX + 1]][0])
            # Can be hexadecimal (with leading 0x) or decimal
            # Ref: https://floodlight.atlassian.net/wiki/display/floodlightcontroller/Static+Flow+Pusher+API
        logger.debug(flow1)  # LOG
        pusher.set(flow1)


def Init_Basic_FlowEntries():
    """ Initialize basic flow entries: CONTROLLER PACKET-IN """

    # Push flow entries like:
    # PACKETIN: sudo ovs-ofctl add-flow datanet1 priority=49999,tcp,tp_dst=13562,actions=controller:max_len=1500
    # ARP: ovs-ofctl add-flow s1 dl_type=0x806,nw_proto=1,actions=flood // 0x806 for ARP packets, proto = 1 for ARP reqs

    # Command:
    # ovs-ofctl -O OpenFlow13 add-flow tcp:192.168.109.215:6666 priority=16666,tcp,tp_dst=13562,actions=controller:max_len=1500
    # Prerequisite: sudo ovs-ofctl set-controller BRIDGE tcp:192.168.109.214:6653 ptcp:6666

    for ServerIP in List_HostToInstallBasicEntries:
        cmdline = "ovs-ofctl -O OpenFlow13 add-flow tcp:" + ServerIP + ":6666 priority=2,tcp,tp_dst=13562,actions=controller:max_len=1000"  # add drop later to avoid flooding
        out = runcommand(cmdline)
        # cmdline = "ovs-ofctl -O OpenFlow13 dump-flows tcp:" + ServerIP + ":6666"
        # out = runcommand(cmdline)

    logger.info("Basic flow entries installed.")


def PreconfigureFlowtable():
    """ Run the Flow Table Pre-configuration for the SDN system in order to boost initial response time """

    # Convert the matrix to numpy matrix
    length = len(Mat_BW_Current)
    Mat_BW_Numpy = np.zeros(shape=(length, length))
    List_SwitchAndHosts = ["" for x in range(length)]
    RevList = defaultdict(lambda: int)

    # Prepare 2 lists to store host/switch no.
    Counter = 0
    for L1 in Mat_BW_Cap_MASK:
        List_SwitchAndHosts[Counter] = L1
        RevList[L1] = Counter
        Counter += 1

    for L1 in Mat_BW_Cap_MASK:
        L2 = Mat_BW_Cap_MASK[L1]
        for L3 in L2:
            if L2[L3] > 0.0:
                Mat_BW_Numpy[RevList[L1]][RevList[L3]] = Mat_BW_Cap[L1][L3]  # Directly assign bandwidth capacity value

    CountOfHosts = len(List_HostToConfig)

    for i in range(0, CountOfHosts-1):
        for j in range(i+1, CountOfHosts):
            # Calculate WSP
            G = nx.from_numpy_matrix(Mat_BW_Curr_DJ_Numpy, create_using=nx.DiGraph())  # Create graph
            path_numerical = nx.dijkstra_path(G, RevList[List_HostToConfig[i]], RevList[List_HostToConfig[j]])  # Run Dijkstra

            # Convert the numerical result to Node(SW/Host)
            path = ['' for x in range(len(path_numerical))]
            Counter = 0
            for element in path_numerical:
                path[Counter] = List_SwitchAndHosts[element]
                Counter += 1

            logger.info('Setting up route: ' + str(path))
            att = {}
            att['tcp_src'] = path[0]
            att['tcp_dst'] = path[-1]
            PushFlowMod(path, att)

    # Pseudocode for this:
    # for i = 0:CountOfHosts-2
    #     for j = i+1:CountOfHosts-1
    #         Calculate shortest path using link bw matrix
    #         Assign flow entries, Print the result
    #         multiply link on link bw matrix by 1.1

    return 1


def runcommand(cmdline):
    logger.info("Command line: " + cmdline)
    output = os.popen(cmdline)
    out = output.read()
    logger.info("Execution result: " + out)

    return out


