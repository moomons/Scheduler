#!/usr/bin/env python
# coding: utf-8

"""
PyCon

Code completely rewritten by mons in a modern and efficient manner
"""

from collections import defaultdict
from pandas import *
import json
import pycon_def
import pprint


Mat_Links = pycon_def.mat_links_bw_init()

print DataFrame(Mat_Links).T.fillna(0)
