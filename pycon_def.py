"""
PyCon
def and config

Stores most global settings and functions

by mons
"""

from collections import defaultdict
import json
import urllib2
import pprint
from pandas import *
from datetime import datetime, timedelta
import threading
import networkx as nx
import numpy as np


BEGIN = 0  # -3 if you want compact debug output, but this WILL impact the dijkstra


# Configurations and global variables
# IP and Port config
# floodlight_host = '192.168.109.214'
Floodlight_IP = '127.0.0.1'
Floodlight_Port = 8080


URL_REST_API_switch_links = 'http://%s:%d/wm/topology/links/json' % (Floodlight_IP, Floodlight_Port)
URL_REST_API_host2switch_links = 'http://%s:%d/wm/device/' % (Floodlight_IP, Floodlight_Port)
URL_REST_API_portdesc_BW = 'http://%s:%d/wm/core/switch/all/port-desc/json' % (Floodlight_IP, Floodlight_Port)
URL_REST_API_Current_BW = 'http://%s:%d/wm/statistics/bandwidth/all/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/statistics/bandwidth/all/all/json|pjt
URL_REST_API_Flow_List = 'http://%s:%d/wm/staticflowpusher/list/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/list/all/json|pjt
URL_REST_API_Flow_Mod = 'http://%s:%d/wm/staticflowpusher/json' % (Floodlight_IP, Floodlight_Port)
# curl -X POST -d '{"switch": "00:00:00:00:00:00:00:02", "name":"flow-mod-1", "cookie":"0", "priority":"33000", "in_port":"2","active":"true", "actions":"output=1"}' http://127.0.0.1:8080/wm/staticflowpusher/json
URL_REST_API_Flow_Clear = 'http://%s:%d/wm/staticflowpusher/clear/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/clear/all/json|pjt


Mat_Links = defaultdict(lambda: defaultdict(lambda: None))
Mat_SWHosts = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Cap = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Cap_MASK = defaultdict(lambda: defaultdict(lambda: None))


Lock_Get_Current_Bps = threading.Lock()
Mat_BW_Current = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Curr_LastUpd = datetime.now() - timedelta(10)


def Get_JSON_From_URL(url):
    try:
        result = json.loads(urllib2.urlopen(url).read())
    except urllib2.HTTPError:
        result = ""
        print 'HTTPError'

    return result


def Init_Mat_Links_And_BW():
    # Initialization

    # Extract switches and nodes links info
    # Now become global

    # Get links between switches
    API_Result = Get_JSON_From_URL(URL_REST_API_switch_links)
    # curl 127.0.0.1:8080/wm/topology/links/json|pjt
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        for EachElem in API_Result:
            Mat_Links[EachElem['src-switch'][BEGIN:]][EachElem['src-port']] = \
                [EachElem['dst-switch'][BEGIN:], EachElem['dst-port']]
            Mat_Links[EachElem['dst-switch'][BEGIN:]][EachElem['dst-port']] = \
                [EachElem['src-switch'][BEGIN:], EachElem['src-port']]
            Mat_SWHosts[EachElem['src-switch'][BEGIN:]][EachElem['dst-switch'][BEGIN:]] = \
                [EachElem['src-port'], EachElem['dst-port']]
            Mat_SWHosts[EachElem['dst-switch'][BEGIN:]][EachElem['src-switch'][BEGIN:]] = \
                [EachElem['dst-port'], EachElem['src-port']]
            # MARK: REMOVE [BEGIN:] before using this script in production environments
    except KeyError:
        print 'KeyError: Are you sure the FL is up?'

    # Get links between hosts
    API_Result = Get_JSON_From_URL(URL_REST_API_host2switch_links)
    # curl 127.0.0.1:8080/wm/device/|pjt
    if len(API_Result) == 0:
        print 'Error: No hosts detected. Please init the hosts before running this script. For example: pingall'
        exit(-1)
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        for EachElem in API_Result:
            if len(EachElem['ipv4'][0]) == 0:
                print 'Error: Host IPv4 address not ready yet. Please wait a while after pingall.'
                exit(-1)
            InEachE = EachElem['attachmentPoint'][0]  # Extract the dict inside the list
            Mat_Links[InEachE['switchDPID'][BEGIN:]][InEachE['port']] = \
                [EachElem['ipv4'][0][BEGIN:], 0]
            Mat_Links[EachElem['ipv4'][0][BEGIN:]][0] = \
                [InEachE['switchDPID'][BEGIN:], InEachE['port']]
            Mat_SWHosts[InEachE['switchDPID'][BEGIN:]][EachElem['ipv4'][0][BEGIN:]] = \
                [InEachE['port'], 0]
            Mat_SWHosts[EachElem['ipv4'][0][BEGIN:]][InEachE['switchDPID'][BEGIN:]] = \
                [0, InEachE['port']]
    except KeyError:
        print 'KeyError: Are you sure the FL is up?'

    # Get BW
    API_Result = Get_JSON_From_URL(URL_REST_API_portdesc_BW)
    # curl 127.0.0.1:8080/wm/core/switch/all/port-desc/json|pjt
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        for EachElem in API_Result:
            InEachE = API_Result[EachElem]['portDesc']
            EachElem = EachElem[BEGIN:]

            for InInEachE in InEachE:
                if InInEachE['portNumber'] == u'local':
                    continue
                CurrVal = Mat_Links[EachElem][int(InInEachE['portNumber'])]
                if CurrVal is None:
                    print 'Error: Host not found. Please pingall. Hosts down for long time inactivity'
                    exit(-1)
                if isinstance(CurrVal[0], list):
                    continue
                else:
                    Speed_In_Mbps = int(InInEachE['currSpeed']) / 1000
                    Mat_Links[EachElem][int(InInEachE['portNumber'])] = \
                        [CurrVal, Speed_In_Mbps]
                    Mat_Links[CurrVal[0]][CurrVal[1]] = \
                        [Mat_Links[CurrVal[0]][CurrVal[1]], Speed_In_Mbps]
                    Mat_BW_Cap[EachElem][CurrVal[0]] = Speed_In_Mbps
                    Mat_BW_Cap[CurrVal[0]][EachElem] = Speed_In_Mbps
                    Mat_BW_Cap_MASK[EachElem][CurrVal[0]] = 1.0
                    Mat_BW_Cap_MASK[CurrVal[0]][EachElem] = 1.0
    except KeyError:
        print 'KeyError: Are you sure the FL is up?'

    return Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK


def Get_Current_Bps():
    """Get Current Bps"""

    global Mat_BW_Curr_LastUpd
    if (datetime.now() - Mat_BW_Curr_LastUpd).total_seconds() < 2:  # A method to compare date
        # if it hasn't been more than 2s before last updated, just return the old dict
        # print 'Old one :)'
        return Mat_BW_Current

    Lock_Get_Current_Bps.acquire()  # Lock to sync

    API_Result = Get_JSON_From_URL(URL_REST_API_Current_BW)
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))

    try:
        for EachElem in API_Result:
            if EachElem['port'] == u'local':
                continue
            # pprint.pprint(EachElem)

            Mat_BW_Curr_LastUpd = datetime.strptime(EachElem['updated'], '%a %b %d %H:%M:%S %Z %Y')

            src_machine = EachElem['dpid'][BEGIN:]  # Source machine
            src_port = int(EachElem['port'])  # Source port
            Mbps_out = int(EachElem['bits-per-second-tx']) / 1000000  # Egress
            Mbps_in = int(EachElem['bits-per-second-rx']) / 1000000  # Ingress
            dst_machine = Mat_Links[src_machine][src_port][0][0]
            # dst_port = Mat_Links[src_machine][src_port][0][1]

            Mat_BW_Current[src_machine][dst_machine] = Mbps_out
            Mat_BW_Current[dst_machine][src_machine] = Mbps_in
    except KeyError:
        print 'KeyError: Are you sure the FL is up?'

    Lock_Get_Current_Bps.release()  # Unlock

    return Mat_BW_Current


def Get_Dijkstra_Path(start, end):
    """Difference: Will add some value to non-zero links for shortest path algo"""

    Mat_BW_Current = Get_Current_Bps()

    length = len(Mat_BW_Current)
    Mat_BW_Curr_DJ_Numpy = np.zeros(shape=(length, length))
    List_SwitchAndHosts = ["" for x in range(length)]
    Counter = 0
    RevList = defaultdict(lambda: int)

    for L1 in Mat_BW_Cap_MASK:
        List_SwitchAndHosts[Counter] = L1
        RevList[L1] = Counter
        Counter += 1

    # Check if the start and end is in the list
    if (start not in List_SwitchAndHosts) or (end not in List_SwitchAndHosts):
        print 'Error: Invalid start or end point.'
        return []

    for L1 in Mat_BW_Cap_MASK:
        L2 = Mat_BW_Cap_MASK[L1]
        for L3 in L2:
            if L2[L3] > 0.0:
                Mat_BW_Curr_DJ_Numpy[RevList[L1]][RevList[L3]] = Mat_BW_Current[L1][L3] + 1.0

    G = nx.from_numpy_matrix(Mat_BW_Curr_DJ_Numpy, create_using=nx.DiGraph())
    path_numerical = nx.dijkstra_path(G, RevList[start], RevList[end])

    path = ['' for x in range(len(path_numerical))]
    Counter = 0
    for element in path_numerical:
        path[Counter] = List_SwitchAndHosts[element]
        Counter += 1

    return path


