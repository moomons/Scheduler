
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




# LOGGING
import logging
logger = logging.getLogger('PyCon')  # create logger
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()  # create console handler and set level to debug
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # create formatter
ch.setFormatter(formatter)  # add formatter to ch
logger.addHandler(ch)  # add ch to logger


import logging.handlers
LOG_FILE = 'Logfile' + '.log'

handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=998)
# fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
fmt = '%(asctime)s - %(levelname)s - %(message)s'

formatter = logging.Formatter(fmt)   # instantiate formatter
handler.setFormatter(formatter)      # add formatter to handler

fileLogger = logging.getLogger('PyCon')  # get logger
fileLogger.addHandler(handler)           # add handler to fileLogger
fileLogger.setLevel(logging.DEBUG)

fileLogger.info('fileLogger started')
# fileLogger.debug('first debug message')
