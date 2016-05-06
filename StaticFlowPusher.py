"""
Reference: http://blog.csdn.net/fei_zodiac/article/details/24706313
"""

import httplib
from pycon_def import *
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


def PushFlowMod(route, att, queue=0):
    """ Send Flow Mod Message to switches, one by one """

    global FlowMod_n
    pusher = StaticFlowPusher(Floodlight_IP)  # Controller IP

    for INDEX in range(1, len(route) - 1):
        print INDEX
        FlowMod_n += 1
        # Setup the Flow Entry for route[INDEX] to route[INDEX+1]
        if INDEX < len(route) - 1:
            flow1 = {
                "name": "pycon-flow-" + str(FlowMod_n),
                "switch": route[INDEX],
                "cookie": "0",
                "priority": "39767",
                "active": "true",
                "idle_timeout": "50",  # DEBUG 50. Release 5
                "in_port": str(Mat_SWHosts[route[INDEX - 1]][route[INDEX]][1]),
                "eth_type": "0x0800",  # IPv4
                "ip_proto": "6",  # TCP
                "ipv4_src": att['ip_src'],
                "ipv4_dst": att['ip_dst'],
                # "ip_tos": "1",
                "tcp_src": att['tcp_src'],
                "tcp_dst": att['tcp_dst'],
                }
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
    # TODO: if possible, push flow entries like:
    # PACKETIN: sudo ovs-ofctl add-flow datanet1 priority=49999,tcp,tp_dst=13562,actions=controller:max_len=1500 && sudo ovs-ofctl dump-flows datanet1
    # ARP: sh ovs-ofctl add-flow s1 dl_type=0x806,nw_proto=1,actions=flood // 0x806 for ARP packets, proto = 1 for ARP requests

    # Simply copied the DICT from VSCtlRemote, actually we are just using the IP
    DICT = {
        "192.168.109.214": {"eth1", "eth2", "eth3", "eth4"},
        "192.168.109.215": {"eth1", "eth2", "eth3", "eth4"},
        "192.168.109.224": {"eth1", "eth2"},
        "192.168.109.225": {"eth1", "eth2"},
    }

    # Viable command:
    # ovs-ofctl -O OpenFlow13 add-flow tcp:192.168.109.215:6666 priority=16666,tcp,tp_dst=13562,actions=controller:max_len=1500
    # FIRST RUN: sudo ovs-ofctl set-controller BRIDGE tcp:192.168.109.214:6653 ptcp:6666
    for ServerIP in DICT:
        cmdline = "ovs-ofctl -O OpenFlow13 add-flow tcp:" + ServerIP + ":6666 priority=16666,tcp,tp_dst=13562,actions=controller:max_len=1500"
        out = runcommand(cmdline)
        cmdline = "ovs-ofctl -O OpenFlow13 dump-flows tcp:" + ServerIP + ":6666"
        out = runcommand(cmdline)


    # MARK: This is a failed attempt using FL StaticFlowPusher
    # pusher = StaticFlowPusher(Floodlight_IP)  # Controller IP
    # for element in Set_Switches_DPID:
    #     # dl_type=0x806,nw_proto=1,actions=flood
    #     flow1 = {
    #         "name": "pycon-flow-ARP-" + element,
    #         "switch": element,
    #         # "cookie": "0",
    #         "priority": "19767",
    #         "active": "true",
    #         "eth_type": "0x0806",  # ARP
    #         # "ip_proto": "1",  # ICMPv4?
    #         "actions": "flood"
    #     }
    #     logger.debug(flow1)  # LOG
    #     pusher.set(flow1)

    logger.info("Basic flow entries pushed.")


def runcommand(cmdline):
    logger.info("Command line: " + cmdline)
    output = os.popen(cmdline)
    out = output.read()
    logger.info("Execution result: " + out)

    return out


