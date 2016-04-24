#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from pycon_def import *
from StaticFlowPusher import *


Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK = Init_Mat_Links_And_BW()

print 'Matrix of Bandwidth Capacity'
print DataFrame(Mat_BW_Cap).T.fillna(0)

print 'Matrix of Bandwidth Capacity (0/1 Masked)'
print DataFrame(Mat_BW_Cap_MASK).T.fillna(0)

# Mat_BW_Current = Get_Current_Bps()
# print 'Matrix of Current Bandwidth Capacity (in Mbps)'
# print DataFrame(Mat_BW_Current).T.fillna(0)

# Current Bandwidth weighted Dijkstra
print Get_Dijkstra_Path('10.0.0.1', '10.0.0.4')

# StaticFlowPusherTest()
