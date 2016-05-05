"""

PyCon

Functions and configs

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
from scipy import *
from pycon_cfg import *


BEGIN = 0  # Set to -3 if you want to have pretty matrix debug output. However beware of duplicates


# MARK: The dict below is placed to mitigate the MAC-only problem (FL only adds MAC to its info panel) in our topology
Dict_KnownMACtoIPv4 = {
    'f8:0f:41:f4:2a:1b': '10.0.0.201',
    'f8:0f:41:f6:63:41': '10.0.0.211',
    'f8:0f:41:f6:68:4e': '10.0.0.212',
    'f8:0f:41:f6:68:4b': '10.0.0.213',
}

# MARK: For mininet debugging
# Dict_KnownMACtoIPv4 = {
#     "00:00:00:00:00:01": "10.0.0.1",
#     "00:00:00:00:00:02": "10.0.0.2",
#     "00:00:00:00:00:03": "10.0.0.3",
#     "00:00:00:00:00:04": "10.0.0.4",
# }


URL_REST_API_switch_links = 'http://%s:%d/wm/topology/links/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/topology/links/json|pjt
URL_REST_API_host2switch_links = 'http://%s:%d/wm/device/' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/device/|pjt
URL_REST_API_portdesc_BW = 'http://%s:%d/wm/core/switch/all/port-desc/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/core/switch/all/port-desc/json|pjt
URL_REST_API_Current_BW = 'http://%s:%d/wm/statistics/bandwidth/all/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/statistics/bandwidth/all/all/json|pjt
URL_REST_API_Flow_List = 'http://%s:%d/wm/staticflowpusher/list/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/list/all/json|pjt
URL_REST_API_Flow_Mod = 'http://%s:%d/wm/staticflowpusher/json' % (Floodlight_IP, Floodlight_Port)
# curl -X POST -d '{"switch": "00:00:00:00:00:00:00:02", "name":"test-mod-1", "cookie":"0", "priority":"33000", "in_port":"2","active":"true", "actions":"output=1"}' http://127.0.0.1:8080/wm/staticflowpusher/json
URL_REST_API_Flow_Clear = 'http://%s:%d/wm/staticflowpusher/clear/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/clear/all/json|pjt


Set_Switches_DPID = set()
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
        logger.error('Failed to GET REST API. \
            Please make sure that FL controller is up and running. \
            And you have set the correct IP and Port.')

    return result


def Init_Mat_Links_And_BW():
    """ Initialize Links and Bandwidth Matrices """
    global Set_Switches_DPID

    # Get links between switches
    API_Result = Get_JSON_From_URL(URL_REST_API_switch_links)
    if len(API_Result) == 0:
        logger.error('Error: No switches detected. Please start FL and config the switches before running this script.')
        exit(-1)
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        logger.info('Switches: ' + str(len(API_Result)))
        for EachElem in API_Result:
            Set_Switches_DPID.add(EachElem['src-switch'][BEGIN:])
            Set_Switches_DPID.add(EachElem['dst-switch'][BEGIN:])
            Mat_Links[EachElem['src-switch'][BEGIN:]][EachElem['src-port']] = \
                [EachElem['dst-switch'][BEGIN:], EachElem['dst-port']]
            Mat_Links[EachElem['dst-switch'][BEGIN:]][EachElem['dst-port']] = \
                [EachElem['src-switch'][BEGIN:], EachElem['src-port']]
            Mat_SWHosts[EachElem['src-switch'][BEGIN:]][EachElem['dst-switch'][BEGIN:]] = \
                [EachElem['src-port'], EachElem['dst-port']]
            Mat_SWHosts[EachElem['dst-switch'][BEGIN:]][EachElem['src-switch'][BEGIN:]] = \
                [EachElem['dst-port'], EachElem['src-port']]
    except KeyError:
        logger.error('KeyError: Are you sure the FL is up?')
        exit(-1)

    # Get links between hosts
    API_Result = Get_JSON_From_URL(URL_REST_API_host2switch_links)
    if len(API_Result) == 0:
        logger.error('Error: No hosts detected. Please init the hosts before running this script. For example: pingall')
        exit(-1)
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        logger.info('Links between switches and hosts: ' + str(len(API_Result)))
        for EachElem in API_Result:
            if len(EachElem['ipv4']) == 0:
                if EachElem['mac'][0] in Dict_KnownMACtoIPv4:
                    EachElem['ipv4'] = [Dict_KnownMACtoIPv4[EachElem['mac'][0]]]
                else:
                    continue
                    # logger.error('Error: Host IPv4 address not ready yet. Please wait a while after pingall.')
                    # exit(-1)
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
        logger.error('KeyError: Are you sure the FL is up?')
        exit(-1)

    # Get BW
    API_Result = Get_JSON_From_URL(URL_REST_API_portdesc_BW)
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
                    # Maybe the PORT is added but not used, just jump to the next one
                    continue
                    # logger.error('Error: Host not found. Please pingall. Hosts down for long time inactivity')
                    # exit(-1)
                if isinstance(CurrVal[0], list):
                    continue
                else:
                    Speed_In_Mbps = int(InInEachE['currSpeed']) / 1000
                    # Mat_Links[SW/Host A MAC/IP][SW/Host A Port] = [SW/Host B MAC/IP, SW/Host B Port]
                    Mat_Links[EachElem][int(InInEachE['portNumber'])] = \
                        [CurrVal, Speed_In_Mbps]
                    Mat_Links[CurrVal[0]][CurrVal[1]] = \
                        [Mat_Links[CurrVal[0]][CurrVal[1]], Speed_In_Mbps]
                    # Mat_BW_Cap[SW/Host A MAC/IP][SW/Host B MAC/IP] = Speed
                    Mat_BW_Cap[EachElem][CurrVal[0]] = Speed_In_Mbps
                    Mat_BW_Cap[CurrVal[0]][EachElem] = Speed_In_Mbps
                    Mat_BW_Cap_MASK[EachElem][CurrVal[0]] = 1.0
                    Mat_BW_Cap_MASK[CurrVal[0]][EachElem] = 1.0
    except KeyError:
        logger.error('KeyError: Are you sure the FL is up?')
        exit(-1)

    return Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK


def Get_Current_Mbps():
    """ Get Current Speed """

    global Mat_BW_Curr_LastUpd
    # if last updated in less than 2s, just return the old dict
    if (datetime.now() - Mat_BW_Curr_LastUpd).total_seconds() < 2:
        return Mat_BW_Current

    Lock_Get_Current_Bps.acquire()  # Lock to sync

    API_Result = Get_JSON_From_URL(URL_REST_API_Current_BW)
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))

    try:
        for EachElem in API_Result:
            if EachElem['port'] == u'local':
                continue
            # pprint.pprint(EachElem)

            src_machine = EachElem['dpid'][BEGIN:]  # Source machine
            src_port = int(EachElem['port'])  # Source port
            if Mat_Links[src_machine][src_port] is None:
                continue  # There is a possibility that some unconnected ports will show up in the API_Result.
            Mbps_out = int(EachElem['bits-per-second-tx']) / 1000000  # Egress
            Mbps_in = int(EachElem['bits-per-second-rx']) / 1000000  # Ingress
            dst_machine = Mat_Links[src_machine][src_port][0][0]
            # dst_port = Mat_Links[src_machine][src_port][0][1]

            Mat_BW_Current[src_machine][dst_machine] = Mbps_out
            Mat_BW_Current[dst_machine][src_machine] = Mbps_in

            Mat_BW_Curr_LastUpd = datetime.strptime(EachElem['updated'], '%a %b %d %H:%M:%S %Z %Y')
    except KeyError:
        logger.error('KeyError: Are you sure the FL is up?')
        exit(-1)

    Lock_Get_Current_Bps.release()  # Unlock

    # Write the speed matrix to a log file for BW usage analysis
    fileLogger.info("Current Mbps:" + str(Mat_BW_Current))

    return Mat_BW_Current


def Get_Dijkstra_Path(start, end):
    """ Use Dijkstra to calculate a route. The weight is current bw. """

    Mat_BW_Current = Get_Current_Mbps()

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
    if (start not in List_SwitchAndHosts) or (end not in List_SwitchAndHosts) or (start == end):
        logger.error('Error in Dijkstra: Invalid start or end point.')
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


# TODO: Half way there
def Get_SEBF_Path(start, end, flow_size):
    """ Use SEBF to plan a route and limit the flow rate. flow_size is in Byte """

    Mat_BW_Current = Get_Current_Mbps()  # This result is in Mbps

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
    if (start not in List_SwitchAndHosts) or (end not in List_SwitchAndHosts) or (start == end):
        logger.error('Error in SEBF-Dijkstra: Invalid start or end point.')
        return []

    for L1 in Mat_BW_Cap_MASK:
        L2 = Mat_BW_Cap_MASK[L1]
        for L3 in L2:
            if L2[L3] > 0.0:
                # Get remaining MB/s
                Mat_BW_Curr_DJ_Numpy[RevList[L1]][RevList[L3]] = Mat_BW_Cap[L1][L3] - Mat_BW_Current[L1][L3] / 8.0

    Mat_FlSize_DIV_BW_Numpy = flow_size / 1000000. / Mat_BW_Curr_DJ_Numpy
    Mat_FlSize_DIV_BW_Numpy[where(isinf(Mat_FlSize_DIV_BW_Numpy))] = 0.0  # Replace Inf with zeros

    G = nx.from_numpy_matrix(Mat_FlSize_DIV_BW_Numpy, create_using=nx.DiGraph())
    path_numerical = nx.dijkstra_path(G, RevList[start], RevList[end])

    path = ['' for x in range(len(path_numerical))]
    Counter = 0
    for element in path_numerical:
        path[Counter] = List_SwitchAndHosts[element]
        Counter += 1

    return path


