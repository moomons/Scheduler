
"""

Stores some configurations and loggers for PyCon

"""

from enum import Enum

# Configurations and global variables
# IP and Port config
# floodlight_host = '192.168.109.214'
Floodlight_IP = '127.0.0.1'
Floodlight_Port = 8080


class SchedulingAlgo(Enum):
    Weighted_Shortest_Path = 1
    SEBF = 2
    More = 3

CurrentSchedulingAlgo = SchedulingAlgo.SEBF


# LOGGING

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='pyconLog.log',
                    filemode='w')
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # create formatter
# fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
# WARNING: Will overwrite the last log file!

console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)

logging.getLogger('').addHandler(console)

logging.info('Application started.')

logger = logging.getLogger('PyCon Main')
fileLogger = logging.getLogger('BW Matrix')

# Ref: http://blog.csdn.net/ghostfromheaven/article/details/8249298

