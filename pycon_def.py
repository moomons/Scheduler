"""
PyCon
def and config

Stores most global settings and functions

by mons
"""

from collections import defaultdict
import json
import urllib2
from pandas import *


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
    Mat_Links = defaultdict(lambda: defaultdict(lambda: None))
    Mat_SWHosts = defaultdict(lambda: defaultdict(lambda: None))
    Mat_BW_Cap = defaultdict(lambda: defaultdict(lambda: None))

    # Get links between switches
    API_Result = Get_JSON_From_URL(URL_REST_API_switch_links)
    # curl 127.0.0.1:8080/wm/topology/links/json|pjt
    # print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
    try:
        for EachElem in API_Result:
            Mat_Links[EachElem['src-switch'][-3:]][EachElem['src-port']] = \
                [EachElem['dst-switch'][-3:], EachElem['dst-port']]
            Mat_Links[EachElem['dst-switch'][-3:]][EachElem['dst-port']] = \
                [EachElem['src-switch'][-3:], EachElem['src-port']]
            Mat_SWHosts[EachElem['src-switch'][-3:]][EachElem['dst-switch'][-3:]] = \
                [EachElem['src-port'], EachElem['dst-port']]
            Mat_SWHosts[EachElem['dst-switch'][-3:]][EachElem['src-switch'][-3:]] = \
                [EachElem['dst-port'], EachElem['src-port']]
            # MARK: REMOVE [-3:] before using this script in production environments
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
            Mat_Links[InEachE['switchDPID'][-3:]][InEachE['port']] = \
                [EachElem['ipv4'][0][-3:], 0]
            Mat_Links[EachElem['ipv4'][0][-3:]][0] = \
                [InEachE['switchDPID'][-3:], InEachE['port']]
            Mat_SWHosts[InEachE['switchDPID'][-3:]][EachElem['ipv4'][0][-3:]] = \
                [InEachE['port'], 0]
            Mat_SWHosts[EachElem['ipv4'][0][-3:]][InEachE['switchDPID'][-3:]] = \
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
            EachElem = EachElem[-3:]

            for InInEachE in InEachE:
                if InInEachE['portNumber'] == u'local':
                    continue
                CurrVal = Mat_Links[EachElem][int(InInEachE['portNumber'])]
                if isinstance(CurrVal[0], list):
                    continue
                else:
                    Speed_In_Gbps = int(InInEachE['currSpeed']) / 1000000
                    Mat_Links[EachElem][int(InInEachE['portNumber'])] = \
                        [CurrVal, Speed_In_Gbps]
                    Mat_Links[CurrVal[0]][CurrVal[1]] = \
                        [Mat_Links[CurrVal[0]][CurrVal[1]], Speed_In_Gbps]
                    Mat_BW_Cap[EachElem][CurrVal[0]] = Speed_In_Gbps
                    Mat_BW_Cap[CurrVal[0]][EachElem] = Speed_In_Gbps
    except KeyError:
        print 'KeyError: Are you sure the FL is up?'

    return Mat_Links, Mat_SWHosts, Mat_BW_Cap


def Get_Current_Bps(Mat_Links):
    Mat_BW_Current = defaultdict(lambda: defaultdict(lambda: None))

    # URL_REST_API_Current_BW
    print 'Get Bps'

