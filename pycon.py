#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from ServerHandler import *


def main():
    print('PyCon, completely rewritten by mons. Initializing ...')

    Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK = Init_Mat_Links_And_BW()

    # print 'Matrix of Network Links'
    # print DataFrame(Mat_Links).T.fillna(0)

    print 'Matrix of Switches and Hosts Link Capacity (in Mbps)'
    print DataFrame(Mat_Links).T.fillna(0)

    # print 'Matrix of Bandwidth Capacity'
    # print DataFrame(Mat_BW_Cap).T.fillna(0)

    # print 'Matrix of Bandwidth Capacity (0/1 Masked)'
    # print DataFrame(Mat_BW_Cap_MASK).T.fillna(0)

    # Mat_BW_Current = Get_Current_Bps()
    # print 'Matrix of Current Bandwidth Capacity (in Mbps)'
    # print DataFrame(Mat_BW_Current).T.fillna(0)

    # Start listening to the POST message from Hadoop MapReduce and FL
    print('Listening at ' + Server_IP + ':' + str(Server_Port))
    httpd = SocketServer.TCPServer((Server_IP, Server_Port), ServerHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # Can do something here
        print 'Quitting.'


if __name__ == '__main__':
    main()

