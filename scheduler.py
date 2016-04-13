# -*- coding: utf-8 -*-
'''
Scheduler

main function :
 1. get topo info
 2. get flow info from ..
 3. get topo status via floodlight rest api
 4. routing 
 5. provision flow table

author : Xiahe Liu

original version date: 2016/03/05

debugged, modified and added functionality by mons
'''

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
import os

#from flow import *
#from routing import *
#from provision import *

DEBUG = 1

#global portinfo,portbytes,mylock
portinfo = defaultdict(lambda:defaultdict(lambda:None))
portbytes = defaultdict(lambda:defaultdict(lambda:None))
topology = topo.topo()  # 1. get topo info
requestflow = []
#mylock = threading.Lock() 


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
        logging.warning("======= POST STARTED =======")
        logging.warning(self.headers)

        length = self.headers.getheader('content-length');
        nbytes = int(length)
        rawdata = self.rfile.read(nbytes)

        logging.warning(rawdata)
        logging.warning(type(rawdata))

        data = json.loads(rawdata)

        logging.warning("======= POST DATA =======")
        # logging.warning(data)
        
        # process the request
        logging.warning("======= coflow_process Starting =======")
        coflow_process(data)

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write('Client: %s\n' % str(self.client_address))
        self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        self.wfile.write('Path: %s\n' % self.path)
        self.wfile.write(rawdata)
        # logging.warning("======= POST END =======")


# get reveiceved and transmitted bytes of each port in each switch
def getPortBytes():
    global portbytes, mylock, DEBUG

    host = '192.168.109.214'
    port = 8080
    if len(sys.argv) >=2:
        host = sys.argv[1]
    if len(sys.argv) >=3:
        port = sys.argv[2]
        
    URL = 'http://%s:%d/wm/core/switch/all/port/json' % (host,port)
    portstatus = simple_json_get(URL)
    #print portstatus
    
    for dpid in portstatus:
        for j in portstatus[dpid]['port_reply'][0]['port']:
            portnum = j['portNumber']
            rbytes = long(j['receiveBytes'])
            tbytes = long(j['transmitBytes'])
            if portbytes[dpid][portnum] == None:
                portbytes[dpid][portnum] = [rbytes,tbytes]
            else:
                portbytes[dpid][portnum][0] = rbytes
                portbytes[dpid][portnum][1] = tbytes

    if DEBUG == 1:
        print 'That was getPortBytes()'
    
        
# calculate average RX and TX during the past interval seconds
def getPortRate(interval):
    global portinfo, portbytes, mylock, DEBUG
    
    while True:
        getPortBytes()
        
        #mylock.acquire()
        for dpid in portbytes:
            for portnum in portbytes[dpid]:
                newrbyte = portbytes[dpid][portnum][0]
                newtbyte = portbytes[dpid][portnum][1]
                #print type(newrbyte), newtbyte
                if portinfo[dpid][portnum] == None:
                    portinfo[dpid][portnum] = [newrbyte/interval,newtbyte/interval,newrbyte,newtbyte]
                else:
                    oldrbyte = portinfo[dpid][portnum][2]
                    oldtbyte = portinfo[dpid][portnum][3]
                    portinfo[dpid][portnum] = [(newrbyte-oldrbyte)/interval,(newtbyte-oldtbyte)/interval,newrbyte,newtbyte]

        if DEBUG == 1:
            print 'Time: ' + str(time.time())  # DEBUG INFO
            print portinfo
            print '======================================== That was getPortRate() LOOP'

        time.sleep(interval)


def flow_table_pusher(flowtables):
    global DEBUG
    
    host = '192.168.109.214'
    port = 8080
    if len(sys.argv) >=2:
        host = sys.argv[1]
    if len(sys.argv) >=3:
        port = sys.argv[2]
        
    url = 'http://%s:%d/wm/staticflowpusher/json' % (host,port)
    
    for flow in flowtables:
        jdata = json.dumps(flow)
        req = urllib2.Request(url, jdata)
        response = urllib2.urlopen(req)
        print response.read()

    if DEBUG == 1:
        print 'That was flow_table_pusher(flowtables)'


def flow_table_delete(flowtables):
    global DEBUG
    
    host = '192.168.109.214'
    port = 8080
    if len(sys.argv) >=2:
        host = sys.argv[1]
    if len(sys.argv) >=3:
        port = sys.argv[2]
        
    url = 'http://%s:%d/wm/staticflowpusher/json' % (host,port)
    
    for flow in flowtables:
        jdata = json.dumps(flow)
        req = urllib2.Request(url, data=jdata)
        req.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(req)
        print response.read()

    if DEBUG == 1:
        print 'That was flow_table_delete(flowtables)'


def flow_table_info(topology, path, pro):
    global DEBUG

    pathnumstr = ""
    for i in path:
        pathnumstr += str(i)
    #print pathnumstr
    
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
        flow = {}
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


def shortest_path():
    global DEBUG

    print 'Doing nothing for now'

    if DEBUG == 1:
        print 'That was shortest_path()'


'''
coflow_process
function:
    handle coflow requests
'''
def coflow_process(request):
    global portinfo, topology, DEBUG

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
    #path = shortest_path()
    path = [5, 3, 1, 4, 7]
    
    # provision flow table
    flows = flow_table_info(topology, path, False)
    logging.warning(flows)
    logging.warning('=======flow pusher end =======')
    requestflow.append(request)
    requestflow.append(flows)
    logging.warning('=======Request process end =======')
    
    logging.warning(requestflow)

    logging.warning("======= That was coflow_process =======")


def main():
    print('Starting Scheduler. Please wait for the listener to get ready ...')
    
    # port RX/TX calculating
    interval = 5

    # Listen port config. Can input host and port as script parameter
    host = '127.0.0.1'
    port = 7999
    if len(sys.argv) >=2:
        host = sys.argv[1]
    if len(sys.argv) >=3:
        port = sys.argv[2]
    
    # Monitor the port rate
    t2 = MyThread(getPortRate, [interval], "RX/TX calculating")
    t2.isDaemon()
    t2.setDaemon(True)
    t2.start()

    # Print the debug info if the DEBUG flag is on
    if DEBUG == 1:
        time.sleep(5)
        logging.warning('main')
        logging.warning(portinfo)
    
    # Start listening to the POST message from Hadoop MapReduce
    print('Listening at ' + host + ':' + str(port))

    Handler = ServerHandler
    httpd = SocketServer.TCPServer((host, port), Handler)

    httpd.serve_forever()


if __name__ == '__main__':
    main()

