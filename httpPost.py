# http post tester

import urllib2
import json
import logging

url = 'http://127.0.0.1:7999'


def http_post():
    for i in range(1, 1):
        logging.warning("Sending request: MR-" + str(i))
        values_MR = {
            'coflowId': 'attempt_1461250880434_0003_m_000017_0',
            'src': 'localhost:13562',  # Test if socket can DNS query this and get 127.0.0.1 first
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


if __name__ == '__main__': 
    http_post()
    logging.warning("httpPost done.")

