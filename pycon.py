#!/usr/bin/env python
# coding: utf-8

from collections import defaultdict
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
URL_REST_API_hosttosw_links = 'http://%s:%d/wm/device/' % (floodlight_host, floodlight_port)
API_Result = pycon_def.json_get_from_url(URL_REST_API_switch_links)

# Print JSON without formatting
# print API_Result

# Pretty print
# print json.dumps(API_Result, sort_keys=True, indent=2, separators=(',', ': '))
# pprint.pprint(API_Result)

# TODO: Extract switches and nodes info from the JSON we just received
node = defaultdict(lambda: None)
try:
    for e in API_Result:
        pprint.pprint(e)
        print(e['src-switch'])
        print(e['src-switch2'])
        break
except KeyError:
    print 'KeyError: The FL return value may have changed or the URL is correct.'

