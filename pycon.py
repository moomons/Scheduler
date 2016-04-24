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


API_Result = pycon_def.json_get_from_url(URL_REST_API_switch_links)
# curl 127.0.0.1:8080/wm/topology/links/json|pjt
# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
try:
    for e in API_Result:
        # pprint.pprint(e)
        Mat_Links[e['src-switch'][-5:]][e['dst-switch'][-5:]] = [e['src-port'], e['dst-port']]
        Mat_Links[e['dst-switch'][-5:]][e['src-switch'][-5:]] = [e['dst-port'], e['src-port']]
        # MARK: REMOVE the [-5:] before running this script in production environments
except KeyError:
    print 'KeyError: Are you sure the FL is up?'


API_Result = pycon_def.json_get_from_url(URL_REST_API_host2switch_links)
# curl 127.0.0.1:8080/wm/device/|pjt
if len(API_Result) == 0:
    print 'Error: No hosts detected. Please init the hosts before running this script. For example: pingall'
    exit(-1)
# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
try:
    for e in API_Result:
        # pprint.pprint(e)
        d = e['attachmentPoint'][0]  # Extract the dict inside the list
        Mat_Links[d['switchDPID'][-5:]][e['ipv4'][0]] = [d['port'], 0]
        Mat_Links[e['ipv4'][0]][d['switchDPID'][-5:]] = [0, d['port']]
        # MARK: REMOVE the [-5:] before running this script in production environments
except KeyError:
    print 'KeyError: Are you sure the FL is up?'


fd = DataFrame(Mat_Links).T.fillna(0)
print fd

