
from collections import defaultdict
import logging
import json
import SimpleHTTPServer
import SocketServer
from pycon_def import *
from StaticFlowPusher import *


Server_IP = '0.0.0.0'
Server_Port = 7999

Dict_RcvdData = defaultdict(lambda: defaultdict(lambda: None))


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
        logging.warning("Got POST data:")
        logging.warning(data)

        # process the request
        logging.warning("Processing data:")
        Process(data)

        # Begin the response
        self.send_response(200)
        self.end_headers()
        # self.wfile.write('Client: %s\n' % str(self.client_address))
        # self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        # self.wfile.write('Path: %s\n' % self.path)
        # self.wfile.write(rawdata)
        # logging.warning("======= POST END =======")


def Process(data):
    # Check if data content already exist in Dict_RcvdData (by 'attempt'):
    # if not exist, write; if exist, write incomplete info

    # if info complete, calc route and call StaticFlowPusher to perform flow mod

    # Current Bandwidth weighted Dijkstra
    # print Get_Dijkstra_Path('10.0.0.1', '10.0.0.4')

    print 'Hi'


def IsRcvdDataComplete():

    return True

