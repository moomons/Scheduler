
import json
import urllib2


def json_get_from_url(url):
    try:
        result = json.loads(urllib2.urlopen(url).read())
    except urllib2.HTTPError:
        result = ""
        print 'HTTPError'

    return result

