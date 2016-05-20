#!/usr/bin/env python
# coding: utf-8

"""

PyCon

An OpenFlow-based Hadoop MapReduce monitor and network controller
Completely rewritten by mons. Works with modified Floodlight and Hadoop MR

"""

from ServerHandler import *
from VSCtlRemote import *
from RatePolling import *
import RunTest


def main():
    logger.info('PyCon: Starting up')
    logger.warning('Please restart PyCon after restarting FL Controller because the flow entries will be wiped.')

    logger.info('Generating Links and Bandwidth Matrices ...')
    Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK = Init_Mat_Links_And_BW()

    # print 'Matrix of Network Links'
    # print DataFrame(Mat_Links).T.fillna(0)
    # print 'Matrix of Switches and Hosts Link Capacity (in Mbps)'
    # print DataFrame(Mat_Links).T.fillna(0)
    # print 'Matrix of Bandwidth Capacity'
    # print DataFrame(Mat_BW_Cap).T.fillna(0)
    # print 'Matrix of Bandwidth Capacity (0/1 Masked)'
    # print DataFrame(Mat_BW_Cap_MASK).T.fillna(0)
    # Mat_BW_Current = Get_Current_Bps()
    # print 'Matrix of Current Bandwidth Capacity (in Mbps)'
    # print DataFrame(Mat_BW_Current).T.fillna(0)

    logger.info('Configuring OVS Switches ...')
    Init_vsctl()

    logger.info('Pre-configuring flow tables ...')
    PreconfigureFlowtable(Mat_BW_Cap)

    # GetPathList('10.0.0.201', '10.0.0.211')
    # Get_Dijkstra_Path('10.0.0.201', '10.0.0.211', SchedulingAlgo.WSP, 998)

    logger.info('Running Offline(Static) Test ...')
    RunTest.RunOffline()

    # logger.info('Installing packet-in flow entries ...')
    # Init_Basic_FlowEntries()
    #
    # # Monitor port rate
    # logger.info('Starting flow rate polling thread ...')
    # thread_poll = MyThread(BandwidthDaemon, [2], "BW Daemon")
    # thread_poll.isDaemon()
    # thread_poll.setDaemon(True)
    # thread_poll.start()
    #
    # # Start listening to the POST message from Hadoop MapReduce and FL
    # logger.info('HTTP Server listening at ' + Server_IP + ':' + str(Server_Port))
    # httpd = SocketServer.TCPServer((Server_IP, Server_Port), ServerHandler)
    # try:
    #     httpd.serve_forever()
    # except KeyboardInterrupt:
    #     # Can do something here
    #     logger.info('Quitting.')


if __name__ == '__main__':
    main()

