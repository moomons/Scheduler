#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import SimpleHTTPServer
import SocketServer
import sys

count = 0


def docount():
    global count
    po_count = count + 1
    logging.warning('po_count = ' + str(po_count))
    count = po_count


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
        data = json.loads(rawdata)
        logging.warning("======= POST DATA =======")
        logging.warning(data)
        dst = self.client_address
        print('Sender: ' + dst[0] + ':' + str(dst[1]))
        docount()

        # Begin the response
        self.send_response(200)
        self.end_headers()
        # self.wfile.write('Client: %s\n' % str(self.client_address))
        # self.wfile.write('User-agent: %s\n' % str(self.headers['user-agent']))
        # self.wfile.write('Path: %s\n' % self.path)
        # self.wfile.write(rawdata)
        # logging.warning("======= POST END =======")


def main():
    host = '0.0.0.0'
    port = 7999
    if len(sys.argv) >=2:
        host = sys.argv[1]
    if len(sys.argv) >=3:
        port = sys.argv[2]

    print('Starting server: ' + host + ':' + str(port))
    Handler = ServerHandler
    httpd = SocketServer.TCPServer((host, port), Handler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()
      

if __name__ == '__main__':
    main()
