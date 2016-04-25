# http post tester

import urllib2
import json
import logging
import sys

# url = 'http://127.0.0.1:7999'
host = '127.0.0.1'
port = 7999


def http_post():
    global host, port
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = sys.argv[2]
    url = 'http://' + host + ':' + str(port)
    try:
        for i in range(1, 2):
            logging.warning("Sending request: MR-" + str(i))
            values_MR = {
                'coflowId': 'attempt_1461250880434_0003_m_000017_0',
                'src': '10.0.0.4:13562',  # Test if socket can DNS query this and get 127.0.0.1 first
                'len': 9285750,  # in bytes
                'flowId': 998,
                'dst': 'Sender',
            }
            jdata = json.dumps(values_MR)
            req = urllib2.Request(url, jdata)
            response = urllib2.urlopen(req)
            print response.read()

            logging.warning("Sending request: FL-" + str(i))
            values_FL = {
                'para_map': 'attempt_1461250880434_0003_m_000017_0',  # Test multiple attempts later sep with ','
                'para_job': 'job_1461250880434_0003',  # the 'Real' coflowId
                'srcPort': 40108,  # the most important info here
                'para_reduce': 0,
            }
            jdata = json.dumps(values_FL)
            req = urllib2.Request(url, jdata)
            response = urllib2.urlopen(req)
            print response.read()
    except urllib2.URLError:
        logging.error("Check your connection.")


if __name__ == '__main__': 
    http_post()
    logging.warning("httpPost done.")

