from django.core.exceptions import MiddlewareNotUsed
import re
from django.conf import settings
from url_metric.exports import get_exporter


class UrlMeaningMiddleware(object):
    """
    This middleware matches the requests url and associates a meaning to the url.
    The meaning is composed of 3 variables: response code, http method and url path without parameters
    The variables are appended to each other with colon :. For example 200:GET:/admin.*
    In case of multiple matches, each meaning is calculated only once.
    """
    def __init__(self):
        self.url_patters = getattr(settings, "URL_METRIC_URL_PATTERNS", None)
        if not self.url_patters:
            raise MiddlewareNotUsed()

        self.metric_exporter = get_exporter()

    def metric(self, metric_name, value=1):
        self.metric_exporter.metric(metric_name, value)

    def process_response(self, request, response):
        path = request.path
        status_code = response.status_code
        method = request.method

        match_url = "%s:%s:%s" % (status_code, method, path, )
        metrics = set()
        for k, v in self.url_patters.iteritems():
            if re.match(k, match_url):
                metrics.add(v)

        for metric_name in metrics:
            self.metric(metric_name)

        return response