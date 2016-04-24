#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from pycon_def import *


Mat_Links, Mat_SWHosts, Mat_BW_Cap = Init_Mat_Links_And_BW()
print DataFrame(Mat_BW_Cap).T.fillna(0)

# Mat_BW_Current = Get_Current_Bps(Mat_Links)
# print DataFrame(Mat_BW_Current).T.fillna(0)

