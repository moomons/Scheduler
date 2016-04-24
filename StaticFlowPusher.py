"""
Reference: http://blog.csdn.net/fei_zodiac/article/details/24706313
"""

import httplib
import json


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
        return ret


def StaticFlowPusherTest():
    pusher = StaticFlowPusher('127.0.0.1')  # Controller IP

    n = 0  # make this variable global

    n += 3
    flow1 = {
        "name": "flow-mod-" + str(n),
        "switch": "00:00:00:00:00:00:00:02",
        "cookie": "0",
        # "priority": "32767",
        "active": "true",
        # "idle_timeout": "50",
        # "in_port": "2",
        "eth_type": "0x0800",  # IPv4
        # "ip_proto": "6",  # TCP
        "ipv4_src": "10.0.0.1",
        "ipv4_dst": "10.0.0.2",
        # "ip_tos": "1",
        # "tcp_src": "55555",
        # "tcp_dst": "13562",
        "actions": "output=1"
        }
    # Ref: https://floodlight.atlassian.net/wiki/pages/viewpage.action?pageId=1343518
    
    pusher.set(flow1)

