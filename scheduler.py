#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Scheduler / Python Controller (PyCon)

Xiahe Liu wrote (2016/03/05):
 1. get topo info
 2. get flow info from ..
 3. get topo status via floodlight rest api
 4. routing 
 5. provision flow table

Siyao Meng did(mons):
 All other stuff :P
 More functionalities
"""

import logging
import json
import topo
import SimpleHTTPServer
import SocketServer
import sys
import time
import urllib2
from collections import defaultdict
import threading
from datetime import datetime

# Global variables
DEBUG = 1  # Debug flag

portinfo = defaultdict(lambda: defaultdict(lambda: None))
portbytes = defaultdict(lambda: defaultdict(lambda: None))
topology = topo.topo()  # Get the topo
requestflow = []
# mylock = threading.Lock()

# port RX/TX calculating
interval = 2

# IP and Port config
httpserver_host = '0.0.0.0'
httpserver_port = 7999
# floodlight_host = '192.168.109.214'
floodlight_host = '127.0.0.1'
floodlight_port = 8080


# multi-threading class
class MyThread(threading.Thread):
    def __init__(self, func, args, name=''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
    
    def run(self):
        self.res = apply(self.func, self.args)
    
    def getResult(self):
        return self.res
        

def simple_json_get(url):
    return json.loads(urllib2.urlopen(url).read())


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        logging.warning("======= GET STARTED =======")
        logging.warning(self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        # logging.warning("======= POST STARTED =======")
        # logging.warning(self.headers)
        nbytes = int(self.headers.getheader('content-length'))
        rawdata = self.rfile.read(nbytes)
        # logging.warning(rawdata)
        # logging.warning(type(rawdata))

        data = json.loads(rawdata)
        logging.warning("======= POST DATA =======")
        logging.warning(data)
        
        # process the request
        logging.warning("======= coflow_process Starting =======")
        coflow_process(data)

        # Begin the response
        self.send_response(200)
        self.end_headers()
        # self.wfile.write('Client: %s\n' % str(self.client_address))
        # self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        # self.wfile.write('Path: %s\n' % self.path)
        # self.wfile.write(rawdata)
        # logging.warning("======= POST END =======")


# get received and transmitted bytes of each port in each switch
def getPortBytes():
    URL = 'http://%s:%d/wm/core/switch/all/port/json' % (floodlight_host, floodlight_port)
    # http://192.168.109.214:8080/wm/core/switch/all/port/json
    portstatus = simple_json_get(URL)
    # print portstatus
    
    for dpid in portstatus:
        for j in portstatus[dpid]['port_reply'][0]['port']:
            portnum = j['portNumber']
            rbytes = long(j['receiveBytes'])
            tbytes = long(j['transmitBytes'])
            if portbytes[dpid][portnum] is None:
                portbytes[dpid][portnum] = [rbytes,tbytes]
            else:
                portbytes[dpid][portnum][0] = rbytes
                portbytes[dpid][portnum][1] = tbytes


# calculate average RX and TX during the past interval seconds
def getPortRate(interval):
    while True:
        getPortBytes()
        
        # mylock.acquire()
        for dpid in portbytes:
            for portnum in portbytes[dpid]:
                newrbyte = portbytes[dpid][portnum][0]
                newtbyte = portbytes[dpid][portnum][1]
                # print type(newrbyte), newtbyte
                if portinfo[dpid][portnum] is None:
                    portinfo[dpid][portnum] = [
                        newrbyte/interval,
                        newtbyte/interval,
                        newrbyte,
                        newtbyte]
                else:
                    oldrbyte = portinfo[dpid][portnum][2]
                    oldtbyte = portinfo[dpid][portnum][3]
                    portinfo[dpid][portnum] = [
                        (newrbyte-oldrbyte)/interval,
                        (newtbyte-oldtbyte)/interval,
                        newrbyte,
                        newtbyte]

        if DEBUG == 1:
            print datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print portinfo
            print '===== That was getPortRate() LOOP'

        time.sleep(interval)


def flow_table_pusher(flowtables):
    url = 'http://%s:%d/wm/staticflowpusher/json' % (floodlight_host, floodlight_port)
    
    for flow in flowtables:
        jdata = json.dumps(flow)
        req = urllib2.Request(url, jdata)
        response = urllib2.urlopen(req)
        print response.read()


def flow_table_delete(flowtables):
    url = 'http://%s:%d/wm/staticflowpusher/json' % (floodlight_host, floodlight_port)
    
    for flow in flowtables:
        jdata = json.dumps(flow)
        req = urllib2.Request(url, data=jdata)
        req.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(req)
        print response.read()


def flow_table_info(topology, path, pro):
    pathnumstr = ""
    for i in path:
        pathnumstr += str(i)
    # print pathnumstr
    
    flowtables = []

    for i in range(len(path)-1):
        if i == 0:
            continue
        preNode = path[i-1]
        curNode = path[i]
        nextNode = path[i+1]

        if DEBUG == 1:
            print 'preNode, curNode, nextNode:'
            print preNode, curNode, nextNode
        
        dpid = topology.node[curNode][0]
        inport = topology.adj[preNode][curNode][2]
        outport = topology.adj[curNode][nextNode][1]
        if DEBUG == 1:
            print 'dpid, inport, outport:'
            print dpid, inport, outport

        # set metrics in a flow table
        flow = []
        flow["switch"] = "%s" % dpid
        flow["name"] = "flow-mod-%s%d" % (pathnumstr,curNode)
        flow["cookie"] = "0"
        flow["priority"] = "32768"
        flow["ingress-port"] = "%d" % inport
        flow["active"] = "true"
        flow["actions"] = "output=%d" % outport

        if DEBUG == 1:
            print 'flow:'
            print flow
        flowtables.append(flow)
    if pro: 
        flow_table_pusher(flowtables)

    if DEBUG == 1:
        print 'That was flow_table_info(topology, path, pro).'

    return flowtables


def shortest_path(src, dst):
    print 'That was shortest_path()'
    return [5, 3, 1, 4, 7]


# Handle coflow requests
def coflow_process(request):

    if DEBUG == 1:
        logging.warning('=======port information=======')
        logging.warning(portinfo)

    # get topo status and update topo info
    topology.update_adj_band(portinfo)
        
    # get the topology information for routing  
    routingTopo = topology.get_routing_topo()
    if DEBUG == 1:
        logging.warning('=======routing topo =======')
        logging.warning(routingTopo)

    # TODO: Routing
    src = 5  # should be real input
    dst = 7  # should be real input
    path = shortest_path(src, dst)
    
    # provision flow table
    flows = flow_table_info(topology, path, False)

    # preNode, curNode, nextNode:
    # 5 3 1
    # dpid, inport, outport:
    # 00:00:00:1b:cd:03:04:64 1 3
    # flow:
    # {'name': 'flow-mod-531473', 'ingress-port': '1', 'actions': 'output=3', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:04:64', 'cookie': '0', 'active': 'true'}
    # preNode, curNode, nextNode:
    # 3 1 4
    # dpid, inport, outport:
    # 00:00:00:1b:cd:03:19:90 1 2
    # flow:
    # {'name': 'flow-mod-531471', 'ingress-port': '1', 'actions': 'output=2', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:19:90', 'cookie': '0', 'active': 'true'}
    # preNode, curNode, nextNode:
    # 1 4 7
    # dpid, inport, outport:
    # 00:00:00:1b:cd:03:05:94 3 1
    # flow:
    # {'name': 'flow-mod-531474', 'ingress-port': '3', 'actions': 'output=1', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:05:94', 'cookie': '0', 'active': 'true'}
    # That was flow_table_info(topology, path, pro).

    logging.warning(flows)
    logging.warning('=======flow pusher end =======')

    # WARNING:root:[{'name': 'flow-mod-531473', 'ingress-port': '1', 'actions': 'output=3', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:04:64', 'cookie': '0', 'active': 'true'}, {'name': 'flow-mod-531471', 'ingress-port': '1', 'actions': 'output=2', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:19:90', 'cookie': '0', 'active': 'true'}, {'name': 'flow-mod-531474', 'ingress-port': '3', 'actions': 'output=1', 'priority': '32768', 'switch': '00:00:00:1b:cd:03:05:94', 'cookie': '0', 'active': 'true'}]
    # WARNING:root:=======flow pusher end =======

    requestflow.append(request)
    requestflow.append(flows)
    logging.warning('=======Request process end =======')
    
    logging.warning(requestflow)
    logging.warning("======= That was coflow_process =======")


def main():
    print('Starting Scheduler (PyCon) ...')
    
    # Monitor port rate
    t2 = MyThread(getPortRate, [interval], "RX/TX Calc")
    t2.isDaemon()
    t2.setDaemon(True)
    t2.start()
    
    # Start listening to the POST message from Hadoop MapReduce
    print('Listening at ' + httpserver_host + ':' + str(httpserver_port))

    httpd = SocketServer.TCPServer((httpserver_host, httpserver_port), ServerHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    main()

