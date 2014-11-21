__author__ = 'margus'

import urllib2

class HTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        data = urllib2.HTTPHandler.http_open(self, req)
        if data.code == 200:
            hostname = req.host
            from url_metric import tasks
            tasks.increase_host_count.delay(hostname)

        return data


class HTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        data = urllib2.HTTPSHandler.https_open(self, req)
        if data.code == 200:
            hostname = req.host
            from url_metric import tasks
            tasks.increase_host_count.delay(hostname)

        return data


class UrllibCustomOpener(object):
    def install_custom_opener(self):
        director = urllib2.build_opener(HTTPHandler, HTTPSHandler)
        urllib2.install_opener(director)

custom_opener = UrllibCustomOpener()
custom_opener.install_custom_opener()
