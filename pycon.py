#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from pycon_def import *
from dijkstra import *


print 'Matrix of Bandwidth Capacity (0/1 Masked)'
Mat_Links, Mat_SWHosts, Mat_BW_Cap, Mat_BW_Cap_MASK = Init_Mat_Links_And_BW()
print DataFrame(Mat_BW_Cap_MASK).T.fillna(0)

# print 'Matrix of Current Bandwidth Capacity (in Mbps)'
# Mat_BW_Current = Get_Current_Bps()
# print DataFrame(Mat_BW_Current).T.fillna(0)

print 'Matrix of Current Bandwidth Capacity for Dijkstra (in Mbps)'
Mat_BW_Current_DJ = Get_Current_Bps_For_Dijkstra()
print DataFrame(Mat_BW_Current_DJ).T.fillna(0)

# Current Bandwidth weighted Dijkstra
print dijkstra_dict2d(Mat_BW_Current_DJ, '0.1', '0.4')
