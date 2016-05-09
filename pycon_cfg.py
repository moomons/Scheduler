
"""

Stores some configurations and loggers for PyCon

"""

from enum import Enum

# Configurations and global variables
# IP and Port config
# floodlight_host = '192.168.109.214'
Floodlight_IP = '192.168.109.214'
Floodlight_Port = 8080


class SchedulingAlgo(Enum):
    Weighted_Shortest_Path = 1
    SEBF = 2
    More = 3

CurrentSchedulingAlgo = SchedulingAlgo.Weighted_Shortest_Path


# dict: {ServerIP: list of PORTs}
vsctl_port = 6640
Dict_OVSToConfig = {
    "192.168.109.214": {"eth1", "eth2", "eth3", "eth4"},
    "192.168.109.215": {"eth1", "eth2", "eth3", "eth4"},
    "192.168.109.224": {"eth1", "eth2"},
    "192.168.109.225": {"eth1", "eth2"},
}


List_HostToConfig = [
    '10.0.0.201',
    '10.0.0.211',
    '10.0.0.212',
    '10.0.0.213',
]


# LOGGING

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s',
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

