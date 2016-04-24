
from collections import defaultdict
import logging
import json
import SimpleHTTPServer
import SocketServer
import socket
from pycon_def import *
from StaticFlowPusher import *


Server_IP = '0.0.0.0'
Server_Port = 7999

Dict_RcvdData = defaultdict(lambda: defaultdict(lambda: None))


class ServerHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        logger.info("do_GET")
        logger.info(self.headers)
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        logger.info("do_POST")
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
        logger.info("Processing data:")
        Process(data, self.client_address)


def Process(data, sender_client_address):
    # Check if data content already exist in Dict_RcvdData (by 'attempt'):
    # if not exist, write; if exist, write incomplete info
    # if info complete, calc route and call StaticFlowPusher to perform flow mod
    if len(data) == 4:  # The message is from the FL controller
        for attempt in data['para_map'].split(','):
            Dict_RcvdData[attempt]['job'] = data['para_job']
            Dict_RcvdData[attempt]['tcp_src'] = data['srcPort']
            Dict_RcvdData[attempt]['reduce'] = data['para_reduce']
            Dict_RcvdData[attempt]['Timestamp_RcvdFL'] = datetime.now()  # Log
            if Dict_RcvdData[attempt]['tcp_dst'] is not None:
                PerformRouting(Dict_RcvdData[attempt])
                del Dict_RcvdData[attempt]  # WARNING: Not tested! MAY RAISE AN ERROR!
    else:
        # The message is from the Hadoop MR
        attempt = data['coflowId']
        spl = data['src'].split(':')
        if not len(spl) == 2:
            logger.error('Error when processing data: Invalid src param. Aborting.')
            return
        Dict_RcvdData[attempt]['ip_src'] = socket.gethostbyname(spl[0])
        Dict_RcvdData[attempt]['ip_dst'] = socket.gethostbyname(str(sender_client_address))  # MARK: NOT Sure about this! Wireshark and test!
        Dict_RcvdData[attempt]['tcp_dst'] = spl[1]
        Dict_RcvdData[attempt]['flowLength'] = data['len']
        Dict_RcvdData[attempt]['Timestamp_RcvdHadoopMR'] = datetime.now()  # Log
        if Dict_RcvdData[attempt]['tcp_src'] is not None:
            PerformRouting(Dict_RcvdData[attempt])
            del Dict_RcvdData[attempt]  # WARNING: Not tested! MAY RAISE AN ERROR!

    logger.info('Data processing done.')


# def IsRcvdDataComplete():
#     return True


def PerformRouting(att):
    """ Finally, Do the Routing! """
    logger.info(att)  # Log

    # MARK: Different scheduling algorithm will result in different route!
    route = Get_Dijkstra_Path(att['ip_src'], att['ip_dst'])  # Change this func when testing diff routing strategy

    logger.info('Route: ' + str(route))
    if len(route) < 3:
        logger.error('Routing failed. Should at least be: Host-SW-Host Please check FL. And perform pingall.')
        return -1

    return PushFlowMod(route, att)

