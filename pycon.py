#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from collections import defaultdict
from pandas import *
import json
import pycon_def
import pprint

# Configurations and global variables
# IP and Port config
# floodlight_host = '192.168.109.214'
floodlight_host = '127.0.0.1'
floodlight_port = 8080

# Initialization
# Extract switches and nodes links info
Mat_Links = defaultdict(lambda: defaultdict(lambda: None))

URL_REST_API_switch_links = 'http://%s:%d/wm/topology/links/json' % (floodlight_host, floodlight_port)
URL_REST_API_host2switch_links = 'http://%s:%d/wm/device/' % (floodlight_host, floodlight_port)
URL_REST_API_portdesc_BW = 'http://%s:%d/wm/core/switch/all/port-desc/json' % (floodlight_host, floodlight_port)

# Get links between switches
API_Result = pycon_def.json_get_from_url(URL_REST_API_switch_links)
# curl 127.0.0.1:8080/wm/topology/links/json|pjt
# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
try:
    for EachElem in API_Result:
        Mat_Links[EachElem['src-switch'][-3:]][EachElem['src-port']] = [EachElem['dst-switch'][-3:], EachElem['dst-port']]
        Mat_Links[EachElem['dst-switch'][-3:]][EachElem['dst-port']] = [EachElem['src-switch'][-3:], EachElem['src-port']]
        # MARK: REMOVE the [-3:] before running this script in production environments
except KeyError:
    print 'KeyError: Are you sure the FL is up?'

# Get links between hosts
API_Result = pycon_def.json_get_from_url(URL_REST_API_host2switch_links)
# curl 127.0.0.1:8080/wm/device/|pjt
if len(API_Result) == 0:
    print 'Error: No hosts detected. Please init the hosts before running this script. For example: pingall'
    exit(-1)
# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
try:
    for EachElem in API_Result:
        InEachE = EachElem['attachmentPoint'][0]  # Extract the dict inside the list
        Mat_Links[InEachE['switchDPID'][-3:]][InEachE['port']] = [EachElem['ipv4'][0][-3:], 0]
        Mat_Links[EachElem['ipv4'][0][-3:]][0] = [InEachE['switchDPID'][-3:], InEachE['port']]
except KeyError:
    print 'KeyError: Are you sure the FL is up?'

# Get BW
API_Result = pycon_def.json_get_from_url(URL_REST_API_portdesc_BW)
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
                Mat_Links[EachElem][int(InInEachE['portNumber'])] = [CurrVal, int(InInEachE['currSpeed']) / 1000000]
                # print DataFrame(Mat_Links).T.fillna(0)
                Mat_Links[CurrVal[0]][CurrVal[1]] = [Mat_Links[CurrVal[0]][CurrVal[1]], int(InInEachE['currSpeed']) / 1000000]
                # print DataFrame(Mat_Links).T.fillna(0)
except KeyError:
    print 'KeyError: Are you sure the FL is up?'


print DataFrame(Mat_Links).T.fillna(0)
