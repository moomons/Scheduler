
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
    WSP = 1
    SEBF = 2
    More = 3

CurrentSchedulingAlgo = SchedulingAlgo.WSP


BEGIN = 0  # Set to -3 if you want to have pretty matrix debug output. However beware of duplicates


# MARK: The dict below is placed to mitigate the MAC-only problem (FL only adds MAC to its info panel) in our topology
Dict_KnownMACtoIPv4 = {
    'f8:0f:41:f4:2a:1b': '10.0.0.201',
    'f8:0f:41:f6:63:41': '10.0.0.211',
    'f8:0f:41:f6:68:4e': '10.0.0.212',
    'f8:0f:41:f6:68:4b': '10.0.0.213',
}

# MARK: For mininet debugging
# Dict_KnownMACtoIPv4 = {
#     "00:00:00:00:00:01": "10.0.0.1",
#     "00:00:00:00:00:02": "10.0.0.2",
#     "00:00:00:00:00:03": "10.0.0.3",
#     "00:00:00:00:00:04": "10.0.0.4",
# }


URL_REST_API_switch_links = 'http://%s:%d/wm/topology/links/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/topology/links/json|pjt
URL_REST_API_host2switch_links = 'http://%s:%d/wm/device/' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/device/|pjt
URL_REST_API_portdesc_BW = 'http://%s:%d/wm/core/switch/all/port-desc/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/core/switch/all/port-desc/json|pjt
URL_REST_API_Current_BW = 'http://%s:%d/wm/statistics/bandwidth/all/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/statistics/bandwidth/all/all/json|pjt
URL_REST_API_Flow_List = 'http://%s:%d/wm/staticflowpusher/list/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/list/all/json|pjt
URL_REST_API_Flow_Mod = 'http://%s:%d/wm/staticflowpusher/json' % (Floodlight_IP, Floodlight_Port)
# curl -X POST -d '{"switch": "00:00:00:00:00:00:00:02", "name":"test-mod-1", "cookie":"0", "priority":"33000", "in_port":"2","active":"true", "actions":"output=1"}' http://127.0.0.1:8080/wm/staticflowpusher/json
URL_REST_API_Flow_Clear = 'http://%s:%d/wm/staticflowpusher/clear/all/json' % (Floodlight_IP, Floodlight_Port)
# curl 127.0.0.1:8080/wm/staticflowpusher/clear/all/json|pjt


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


List_HostToInstallBasicEntries = [
    "192.168.109.214",
    "192.168.109.215",
    "192.168.109.224",
    "192.168.109.225",
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

