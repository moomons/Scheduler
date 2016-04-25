#!/usr/bin/env python
# coding: utf-8

"""

PyCon

An OpenFlow-based Hadoop MapReduce monitor and network controller
Completely rewritten by mons. Works with modified Floodlight and Hadoop MR

"""

from ServerHandler import *


def main():
    logger.info('Starting up PyCon.')

    logger.info('Initializing Links and Bandwidth Matrices...')
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

    logger.info('Initializing basic flow entries ...')
    Init_Basic_FlowEntries()

    # Start listening to the POST message from Hadoop MapReduce and FL
    logger.info('HTTP Server listening at ' + Server_IP + ':' + str(Server_Port))
    httpd = SocketServer.TCPServer((Server_IP, Server_Port), ServerHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        # Can do something here
        logger.info('Quitting.')


if __name__ == '__main__':
    main()

