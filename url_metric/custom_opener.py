__author__ = 'margus'

import urlparse
import socket
import urllib2
try:
    import requests
except:
    requests = None

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


custom_opener = None
def get_custom_opener():
    global custom_opener
    if not custom_opener:
        custom_opener = urllib2.build_opener(HTTPHandler, HTTPSHandler)

    return custom_opener

def install_custom_opener(custom_opener):
    urllib2.install_opener(custom_opener)


def urlopen(url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, *args, **kwargs):
    """
    Wrapper for urllib2.urlopen

    :param url:
    :param data:
    :param timeout:
    :param args:
    :param kwargs:
    :return:
    """
    custom_opener = get_custom_opener()
    return custom_opener.open(url, data, timeout, *args, **kwargs)

def get(url, *args, **kwargs):
    """
    Wrapper for requests.get
    :param args:
    :param kwargs:
    :return:
    """
    return requests_wrapper(requests.get, url, *args, **kwargs)

def post(url, *args, **kwargs):
    """
    Wrapper for requests.post
    :param args:
    :param kwargs:
    :return:
    """
    return requests_wrapper(requests.post, url, *args, **kwargs)

def put(url, *args, **kwargs):
    """
    Wrapper for requests.put
    :param args:
    :param kwargs:
    :return:
    """
    return requests_wrapper(requests.put, url, *args, **kwargs)

def delete(url, *args, **kwargs):
    """
    Wrapper for requests.delete
    :param args:
    :param kwargs:
    :return:
    """
    return requests_wrapper(requests.delete, url, *args, **kwargs)

def requests_wrapper(method, url, *args, **kwargs):
    """
    Generic requests wrapper
    :param method:
    :param url:
    :param args:
    :param kwargs:
    :return:
    """
    r = method(url, *args, **kwargs)
    if r.status_code == 200:
        parsed = urlparse.urlparse(url)
        hostname = parsed.hostname
        from url_metric import tasks
        tasks.increase_host_count.delay(hostname)
    return r


custom_opener = get_custom_opener()
install_custom_opener(custom_opener)