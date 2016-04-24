#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from collections import defaultdict
from pandas import *
import json
import pprint
from pycon_def import *


Mat_Links, Mat_SWHosts, Mat_BW = Init_Mat_Links_And_BW()

print DataFrame(Mat_BW).T.fillna(0)
