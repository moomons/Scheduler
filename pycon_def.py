"""

PyCon

Stores most main functions

by mons

"""

from collections import defaultdict
import json
import urllib2
# import pprint
from pandas import *
from datetime import datetime, timedelta
import threading
import networkx as nx
import numpy as np
import time
from scipy import *
from pycon_cfg import *


Set_Switches_DPID = set()
Mat_Links = defaultdict(lambda: defaultdict(lambda: None))
Mat_SWHosts = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Cap = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Cap_MASK = defaultdict(lambda: defaultdict(lambda: None))

Lock_Get_Current_Bps = threading.Lock()
Mat_BW_Current = defaultdict(lambda: defaultdict(lambda: None))
Mat_BW_Curr_LastUpd = datetime.now() - timedelta(10)

Lock_Get_Current_Bps_Numpy = threading.Lock()
Mat_BW_Curr_DJ_Numpy = np.zeros(shape=(1, 1))  # MARK: Not sure whether this can be changed later without error
List_SwitchAndHosts = []
RevList = defaultdict(lambda: int)
Mat_BW_Curr_LastUpd_Numpy = Mat_BW_Curr_LastUpd


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
    # MARK: Moved to other def
    # fileLogger.info("Current Mbps:" + str(Mat_BW_Current))
    logger.info("Mat_BW_Current updated.")

    return Mat_BW_Current


def BandwidthDaemon(interval):
    logger.info("Daemon thread started.")
    while True:
        Get_Current_Mbps()
        time.sleep(interval)


def Get_Current_Mbps_Numpy(InputSchAlgo, flow_size=0):
    """ Get Current Speed matrix in numpy format """

    global Mat_BW_Curr_LastUpd_Numpy, Mat_BW_Current, Mat_BW_Curr_DJ_Numpy, List_SwitchAndHosts, RevList
    # if last updated in less than 2s, just return the old dict
    if (datetime.now() - Mat_BW_Curr_LastUpd_Numpy).total_seconds() < 2:
        return Mat_BW_Current, Mat_BW_Curr_DJ_Numpy, List_SwitchAndHosts, RevList

    Lock_Get_Current_Bps_Numpy.acquire()  # Lock

    Mat_BW_Current = Get_Current_Mbps()
    Mat_BW_Curr_LastUpd_Numpy = datetime.now()

    length = len(Mat_BW_Current)
    Mat_BW_Curr_DJ_Numpy = np.zeros(shape=(length, length))
    List_SwitchAndHosts = ["" for x in range(length)]
    RevList = defaultdict(lambda: int)

    # Prepare 2 lists to store host/switch no.
    Counter = 0
    for L1 in Mat_BW_Cap_MASK:
        List_SwitchAndHosts[Counter] = L1
        RevList[L1] = Counter
        Counter += 1

    if InputSchAlgo == SchedulingAlgo.WSP:
        logger.info("Using WSP Algo.")
        for L1 in Mat_BW_Cap_MASK:
            L2 = Mat_BW_Cap_MASK[L1]
            for L3 in L2:
                if L2[L3] > 0.0:
                    Mat_BW_Curr_DJ_Numpy[RevList[L1]][RevList[L3]] = Mat_BW_Current[L1][L3] + 1.0
    elif InputSchAlgo == SchedulingAlgo.SEBF:
        logger.info("Using SEBF Algo.")
        for L1 in Mat_BW_Cap_MASK:
            L2 = Mat_BW_Cap_MASK[L1]
            for L3 in L2:
                if L2[L3] > 0.0:
                    # Get remaining MB/s
                    Mat_BW_Curr_DJ_Numpy[RevList[L1]][RevList[L3]] = Mat_BW_Cap[L1][L3] - Mat_BW_Current[L1][L3] / 8.0
        Mat_BW_Curr_DJ_Numpy_DIV = flow_size / 1000000. / Mat_BW_Curr_DJ_Numpy
        Mat_BW_Curr_DJ_Numpy_DIV[where(isinf(Mat_BW_Curr_DJ_Numpy_DIV))] = 0.0  # Replace Inf with zeros
        Mat_BW_Curr_DJ_Numpy = Mat_BW_Curr_DJ_Numpy_DIV
    else:
        logger.error("Unknown Algo!")
        return []

    Lock_Get_Current_Bps_Numpy.release()  # Unlock

    # Better matrix logging
    fileLogger.info("Current Mbps matrix:\n" + str(Mat_BW_Curr_DJ_Numpy))

    return Mat_BW_Current, Mat_BW_Curr_DJ_Numpy, List_SwitchAndHosts, RevList


def Get_Dijkstra_Path(start, end, ScheAlgo, flow_size=0):
    """ Use Dijkstra to calculate a route. The weight is the current bandwidth. """

    global Mat_BW_Current, Mat_BW_Curr_DJ_Numpy, List_SwitchAndHosts, RevList
    Mat_BW_Current, Mat_BW_Curr_DJ_Numpy, List_SwitchAndHosts, RevList = \
        Get_Current_Mbps_Numpy(ScheAlgo, flow_size)

    # Check if the start and end is in the list
    if (start not in List_SwitchAndHosts) or (end not in List_SwitchAndHosts) or (start == end):
        logger.error('Error in Dijkstra: Invalid start or end point.')
        return []

    G = nx.from_numpy_matrix(Mat_BW_Curr_DJ_Numpy, create_using=nx.DiGraph())  # Create graph
    path_numerical = nx.dijkstra_path(G, RevList[start], RevList[end])  # Run Dijkstra

    # Convert the numerical result to Node(SW/Host)
    path = ['' for x in range(len(path_numerical))]
    Counter = 0
    for element in path_numerical:
        path[Counter] = List_SwitchAndHosts[element]
        Counter += 1

    return path


# Almost the same as Get_Dijkstra_Path()
def Get_SEBF_Path(start, end, ScheAlgo, flow_size):
    """ Use SEBF to plan a route and limit the flow rate. flow_size is in Byte """
    return Get_Dijkstra_Path(start, end, ScheAlgo, flow_size)


