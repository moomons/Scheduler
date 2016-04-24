#!/usr/bin/env python
# coding: utf-8

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


# TODO: Create the topo from FL REST API return info
topo = defaultdict(lambda: defaultdict(lambda: None))

# TODO: Using HTTP POST to get the return value from FL Controller
URL_REST_API_switch_links = 'http://%s:%d/wm/topology/links/json' % (floodlight_host, floodlight_port)
URL_REST_API_host2switch_links = 'http://%s:%d/wm/device/' % (floodlight_host, floodlight_port)
API_Result = pycon_def.json_get_from_url(URL_REST_API_switch_links)

# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))

# Extract switches and nodes links info
Mat_Links = defaultdict(lambda: defaultdict(lambda: None))
try:
    for e in API_Result:
        pprint.pprint(e)
        Mat_Links[e['src-switch']][e['dst-switch']] = [e['src-port'], e['dst-port']]
        Mat_Links[e['dst-switch']][e['src-switch']] = [e['dst-port'], e['src-port']]

        # print(e['src-switch'])
        # print(e['src-port'])
except KeyError:
    print 'KeyError: The FL return value may have changed or the URL is incorrect.'

print Mat_Links

fd = DataFrame(Mat_Links).T.fillna(0)
print fd

