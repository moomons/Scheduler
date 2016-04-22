# http post

import urllib2
import json

    
def http_post():
    url='http://192.168.32.111:7999'
    values ={'coflowId':1,'flowId':1, 'sour':'10.0.0.1', 'dst':'10.0.0.2', 'size':100}
    jdata = json.dumps(values)
    req = urllib2.Request(url, jdata)
    response = urllib2.urlopen(req)
    print response.read()


if __name__ == '__main__': 
    http_post()

