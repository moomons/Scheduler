from collections import defaultdict

class topo(object):
    def __init__(self):
        # hosts & switches
        self.switchNum = 4
        self.hostNum = 4
        self.node = defaultdict(lambda: None)
        # switch[i] = [dpid, mac, ipv4, port]
        # the node whose id <= switchNum is switch node
        # TODO: the 'port' is not effective, can I remove it? Or fix this.
        self.node[1] = ['00:00:00:1b:cd:03:19:90', '00:1b:cd:03:19:90', '192.168.109.224', '45915']
        self.node[2] = ['00:00:00:1b:cd:03:16:ac', '00:1b:cd:03:16:ac', '192.168.109.225', '56741']
        self.node[3] = ['00:00:00:1b:cd:03:04:64', '00:1b:cd:03:04:64', '192.168.109.214', '42058']
        self.node[4] = ['00:00:00:1b:cd:03:05:94', '00:1b:cd:03:05:94', '192.168.109.215', '53878']

        # host[i] = [mac, ipv4, ipv6, attachedswitch, switchport, switchId]
        # the node whose id > switchNum and id <= switchNum + hostNUm is host node
        self.node[5] = ['f8:0f:41:f6:68:4e', '10.0.0.212', 'fe80::fa0f:41ff:fef6:684e', '00:00:00:1b:cd:03:04:64', 1, 3]
        self.node[6] = ['f8:0f:41:f6:68:4b', '10.0.0.213', 'fe80::fa0f:41ff:fef6:684b', '00:00:00:1b:cd:03:04:64', 2, 3]
        self.node[7] = ['f8:0f:41:f6:63:41', '10.0.0.211', 'fe80::fa0f:41ff:fef6:6341', '00:00:00:1b:cd:03:05:94', 1, 4]
        self.node[8] = ['f8:0f:41:f4:2a:1b', '10.0.0.201', 'fe80::72e2:84ff:fe05:6767', '00:00:00:1b:cd:03:05:94', 2, 4]

        # topology
        # adjacency[1][2] = [link_id, outport, inport, bandwidth]
        self.adj = defaultdict(lambda: defaultdict(lambda: None))
        self.defaultband = 1000
        self.adj[1][3] = [1, 1, 3, self.defaultband]
        self.adj[3][1] = [2, 3, 1, self.defaultband]
        self.adj[1][4] = [3, 2, 3, self.defaultband]
        self.adj[4][1] = [4, 3, 2, self.defaultband]
        self.adj[2][3] = [5, 4, 4, self.defaultband]
        self.adj[3][2] = [6, 4, 4, self.defaultband]
        self.adj[2][4] = [7, 5, 4, self.defaultband]
        self.adj[4][2] = [8, 4, 5, self.defaultband]
        
        self.adj[3][5] = [9, 1, 0, self.defaultband]
        self.adj[5][3] = [10, 0, 1, self.defaultband]
        self.adj[3][6] = [11, 2, 0, self.defaultband]
        self.adj[6][3] = [12, 0, 2, self.defaultband]
        self.adj[4][7] = [13, 1, 0, self.defaultband]
        self.adj[7][4] = [14, 0, 1, self.defaultband]
        self.adj[4][8] = [15, 2, 0, self.defaultband]
        self.adj[8][4] = [16, 0, 2, self.defaultband]

        self.topo = defaultdict(lambda: defaultdict(lambda: None))
        # topo[dpid][portnum] = [rate, src, dst]
        self.topo['00:00:00:1b:cd:03:19:90'][1] = [1, 3]  # TX
        self.topo['00:00:00:1b:cd:03:19:90'][2] = [1, 4]  # TX
        self.topo['00:00:00:1b:cd:03:16:ac'][4] = [2, 3]  # TX
        self.topo['00:00:00:1b:cd:03:16:ac'][5] = [2, 4]  # TX
        
        self.topo['00:00:00:1b:cd:03:04:64'][3] = [3, 1]  # TX
        self.topo['00:00:00:1b:cd:03:04:64'][4] = [3, 2]  # TX
        self.topo['00:00:00:1b:cd:03:05:94'][3] = [4, 1]  # TX
        self.topo['00:00:00:1b:cd:03:05:94'][4] = [4, 2]  # TX
        
        self.topo['00:00:00:1b:cd:03:04:64'][1] = [3, 5]  # TX
        self.topo['00:00:00:1b:cd:03:04:64'][2] = [3, 6]  # TX
        self.topo['00:00:00:1b:cd:03:04:64'][11] = [5, 3]  # RX
        self.topo['00:00:00:1b:cd:03:04:64'][12] = [6, 3]  # RX
        
        self.topo['00:00:00:1b:cd:03:05:94'][1] = [4, 7]  # TX
        self.topo['00:00:00:1b:cd:03:05:94'][2] = [4, 8]  # TX
        self.topo['00:00:00:1b:cd:03:05:94'][11] = [7, 4]  # RX
        self.topo['00:00:00:1b:cd:03:05:94'][12] = [8, 4]  # RX
        # self.routingTopo = self.get_routing_topo()


    def update_adj_band(self, portinfo):
        bytes2mb = 1048576
        for dpid in portinfo:
            for portnum in portinfo[dpid]:
                if portnum == 'local':
                    continue
                portnumint = int(portnum)
                if self.topo[dpid][portnumint] == None:
                    continue
                    
                src = self.topo[dpid][portnumint][0]
                dst = self.topo[dpid][portnumint][1]
                self.adj[src][dst][3] = self.defaultband - portinfo[dpid][portnum][1]/bytes2mb

                if (dpid == '00:00:00:1b:cd:03:04:64' or dpid == '00:00:00:1b:cd:03:05:94') and (portnumint ==1 or portnumint ==2):
                    portnumint = portnumint + 10
                    src2 = self.topo[dpid][portnumint][0]
                    dst2 = self.topo[dpid][portnumint][1]
                    self.adj[src2][dst2][3] = self.defaultband - portinfo[dpid][portnum][0]/bytes2mb
        print self.adj
        return True
        
    def get_routing_topo(self):
        # topology with weight infomation
        print "get_routing_topo"
        routingTopo = defaultdict(lambda:defaultdict(lambda:None))
        for i in self.adj:
            for j in self.adj[i]:
                tmp = self.adj[i][j][3]
                if tmp!=0:
                    routingTopo[i][j] = tmp
        #print routingTopo
        return routingTopo
    
    def update_adj(self,src,dst,info,newlink):
        # add a new link or update exist link
        if newlink:
            self.adj[src][dst] = info
        elif self.adj[src][dst] != None:
            self.adj[src][dst] = info
        else:
            raise KeyError

    def update_node_info(self,nodeId,info,newnode):
        # add a new node or update exist node
        if newnode:
            self.node[nodeId] = info
        elif self.node[nodeId] != None:
            self.node[nodeId] = info
        else:
            raise KeyError
            
    
    '''       
    # discard
    # originally wanna to use this get bandwidth from floodlight(bug here,cannot get port information)
    # then update topology information
    def simple_json_get(self, url):
        return json.loads(urllib2.urlopen(url).read())
        
    def get_topo_status(self):
        host = "192.168.109.214"
        port = 8080
        
        for i in self.adj:
            for j in self.adj[i]:
                if j <= i:
                    continue
                swicthId = self.node[i][0]
                portId = self.adj[i][j][1]
                print i,j, swicthId, portId
                URL = "http://%s:%d/wm/statistics/bandwidth/%s/%d/json" % (host,port,swicthId,portId)
                ### need to process the FL bandwidth output !!!!!!!!!!!!!!!!!!!!!
                new = self.simple_json_get(URL)
                
                {
                "bits-per-second-rx": "0",
                "bits-per-second-tx": "0",
                "dpid": "00:00:00:00:00:00:00:01",
                "port": "local",
                "updated": "Wed Feb 17 10:42:20 EST 2016"
                }
                
                print new
                old = self.adj[i][j][3]
                if old != new:
                    info = self.adj[i][j]
                    info[3] = new
                    self.update_topo(i,j,info,False)
    '''
    
def test():
    topology = topo()
    '''
    print topology.node
    print topology.adj
    '''
    
    '''
    info = topology.node[1]
    info[0] = '0000'
    topology.update_node_info(1,info,True)
    print topology.node[1]
    '''
    
    '''
    tmp = topology.get_routing_topo()
    for i in tmp:
        for j in tmp[i]:
            print i, j, tmp[i][j]
    '''
    
    #topology.get_topo_status()
    '''
    try:
        f = open('tmp.txt','r')
    except IOError:
        logging.warning('cannot open file')
    rawdata = f.read()
    data = json.loads(rawdata)
    #print data
    f.close()

    topology.update_adj_band(data)
    '''
    
if __name__ == '__main__':
    test()