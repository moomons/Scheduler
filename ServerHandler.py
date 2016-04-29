
from collections import defaultdict
import logging
import json
import SimpleHTTPServer
import SocketServer
import socket
from pycon_def import *
import threading
from StaticFlowPusher import *


Server_IP = '0.0.0.0'
Server_Port = 7999

Dict_RcvdData = defaultdict(lambda: defaultdict(lambda: None))

# MARK: Fail safe. FL should get dst IP correctly now.
Dict_KnownMRIPtoOFIP = {
    '192.168.109.201': '10.0.0.201',
    '192.168.109.211': '10.0.0.211',
    '192.168.109.212': '10.0.0.212',
    '192.168.109.213': '10.0.0.213',
}


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        logger.info("do_GET")
        logger.info(self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        # logger.info("do_POST")
        # logger.info(self.headers)
        nbytes = int(self.headers.getheader('content-length'))
        rawdata = self.rfile.read(nbytes)
        # logger.info(rawdata)
        # logger.info(type(rawdata))

        data = json.loads(rawdata)
        logger.info("Got POST data:")
        logger.info(data)

        # Begin the response
        self.send_response(200)
        self.end_headers()
        # self.wfile.write('Client: %s\n' % str(self.client_address))
        # self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        # self.wfile.write('Path: %s\n' % self.path)
        # self.wfile.write(rawdata)

        # process the request
        # logger.info("Processing data:")
        Process(data, self.client_address)


def Process(data, sender_client_address):
    """ Process the POST data """

    # Check if data content already exist in Dict_RcvdData (by 'attempt'):
    # if not exist, write; if exist, write incomplete info
    # if info complete, calc route and call StaticFlowPusher to perform flow mod
    if 'srcPort' in data:
        # FL controller message
        for attempt in data['para_map'].split(','):
            Dict_RcvdData[attempt]['job'] = data['para_job']
            if 'ip_dst' in data:
                Dict_RcvdData[attempt]['ip_dst'] = data['ip_dst']
            Dict_RcvdData[attempt]['tcp_src'] = data['srcPort']
            Dict_RcvdData[attempt]['reduce'] = data['para_reduce']
            Dict_RcvdData[attempt]['Timestamp_RcvdFL'] = datetime.now()  # Log
            if Dict_RcvdData[attempt]['tcp_dst'] is not None:
                PerformRouting(Dict_RcvdData[attempt])
                del Dict_RcvdData[attempt]
    elif 'coflowId' in data:
        # MR message
        attempt = data['coflowId']
        spl = data['src'].split(':')
        if not len(spl) == 2:
            logger.error('Error when processing data: Invalid src param. Aborting.')
            return
        Dict_RcvdData[attempt]['ip_src'] = socket.gethostbyname(spl[0])
        Dict_RcvdData[attempt]['ip_dst_MR'] = socket.gethostbyname(str(sender_client_address[0]))  # MARK: Not sure of the correctness
        Dict_RcvdData[attempt]['tcp_dst'] = int(spl[1])
        Dict_RcvdData[attempt]['flowLength'] = data['len']
        Dict_RcvdData[attempt]['Timestamp_RcvdHadoopMR'] = datetime.now()  # Log
        if Dict_RcvdData[attempt]['tcp_src'] is not None:
            PerformRouting(Dict_RcvdData[attempt])
            del Dict_RcvdData[attempt]
    else:
        logger.error("Process: Invalid POST data (from neither FL nor MR")

    # logger.info('Process() done.')


def PerformRouting(att):
    """ Do the Routing """
    logger.info(att)  # Log

    # MARK: Fail safe. FL should get dst IP correctly now.
    # ip_dst is in 10.0.0.0/24 while ip_dst_MR is in 192.168.109.0/24
    if 'ip_dst' not in att:
        if att['ip_dst_MR'] in Dict_KnownMRIPtoOFIP:
            att['ip_dst'] = Dict_KnownMRIPtoOFIP[att['ip_dst_MR']]
        else:
            att['ip_dst'] = att['ip_dst_MR']

    # MARK: Different scheduling algorithm will result in different route!
    route = Get_Dijkstra_Path(att['ip_src'], att['ip_dst'])  # Change this func when testing diff routing strategy

    logger.info('Route: ' + str(route))
    if len(route) < 3:
        logger.error('Routing failed. Should at least be: Host-SW-Host Please check FL. And perform pingall.')
        return -1

    return PushFlowMod(route, att)

