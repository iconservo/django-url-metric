from url_metric import exports
from django.conf import settings

__author__ = 'margus'

import logging
import urlparse
import socket
import urllib2
try:
    import requests
except:
    requests = None

def metric_request(hostname, method, status_code, path = ''):

    host_with_path = "%s%s" % (hostname, path)
    host_url_metrics = getattr(settings, 'URL_METRIC_HOST_OVERRIDES', {})
    host_url_metric = host_url_metrics.get(host_with_path, hostname)

    metric_name = "External.%s.%s.%s" % (host_url_metric, method, status_code)
    from url_metric.tasks import metric
    metric.delay(metric_name, hostname = host_url_metric)


def get_logger(hostname, path = '', logger_type='debug'):
    host_with_path = "%s%s" % (hostname, path)
    host_url_loggers = getattr(settings, 'URL_METRIC_HOST_OVERRIDES', {})

    host_url_logger_name = host_url_loggers.get(host_with_path, hostname)

    return logging.getLogger("external.%s.%s" % (logger_type, host_url_logger_name))

class WrappedResponse(object):
    def __init__(self, response, content):
        self._read_content = content
        self._wrapped = response

    def __getattr__(self, item):
        return getattr(self._wrapped, item)

    def read(self):
        x = self._read_content
        self._read_content = ''
        return x

class HTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        hostname = req.get_host()
        method = req.get_method()
        url = req.get_full_url()

        parsed = urlparse.urlparse(url)
        path = parsed.path

        data = urllib2.HTTPHandler.http_open(self, req)

        from url_metric import tasks
        tasks.increase_host_count_task.delay(hostname)

        content = data.read()

        logger = get_logger(hostname, path, 'access')
        logger.info(msg="", extra={"url": url, "status_code": data.code, "response_data": content})

        metric_request(hostname, method, data.code, path)

        return WrappedResponse(data, content)


class HTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        hostname = req.get_host()
        method = req.get_method()
        url = req.get_full_url()

        parsed = urlparse.urlparse(url)
        path = parsed.path

        data = urllib2.HTTPSHandler.https_open(self, req)

        from url_metric import tasks
        tasks.increase_host_count_task.delay(hostname)

        content = data.read()

        logger = get_logger(hostname, path, 'access')
        logger.info(msg="", extra={"url": url, "status_code": data.code, "response_data": content})

        metric_request(hostname, method, data.code, path)

        return WrappedResponse(data, content)


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
    response = custom_opener.open(url, data, timeout, *args, **kwargs)
    """
    try:
        custom_opener = get_custom_opener()
        response = custom_opener.open(url, data, timeout, *args, **kwargs)
    except Exception, e:
        parsed = urlparse.urlparse(url)
        hostname = parsed.hostname

        logger = logging.getLogger("external.error.%s" % hostname)
        logger.exception(extra={"url": url})
    """
    return response

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
    parsed = urlparse.urlparse(url)
    hostname = parsed.hostname
    req_method = r.request.method
    path = parsed.path

    metric_request(hostname, req_method, r.status_code, path)

    from url_metric import tasks
    tasks.increase_host_count_task.delay(hostname)

    response_data = getattr(r, "content", None)
    logger = get_logger(hostname, path, 'access')#logging.getLogger("external.access.%s" % hostname)
    logger.info(msg="", extra={"url": url, "status_code": r.status_code, "response_data": response_data})

    return r


custom_opener = get_custom_opener()
install_custom_opener(custom_opener)