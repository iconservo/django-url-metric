#encoding: utf-8
__author__ = 'margus'

from django.conf import settings
import logging

access_logger = logging.getLogger('external.access.Librato')
debug_logger = logging.getLogger('external.debug.Librato')
error_logger = logging.getLogger('external.error.Librato')

MAPPING = {}

# TODO: exporter singleton support
# TODO: custom source
# TODO: rename metric to gauge

def get_exporter():
    exporter_class_name = getattr(settings, "URL_METRIC_EXPORT_ENGINE", None)
    source = getattr(settings, "URL_METRIC_SOURCE", None)
    if not exporter_class_name:
        return None

    cls = MAPPING.get(exporter_class_name, None)
    if not cls:
        return None

    exporter = cls(source=source)

    return exporter


class BaseExporter(object):
    def __init__(self, source):
        self.source = source

    def export(self, metric, value):
        pass

    def save(self):
        pass

    def metric(self, metric, value=1):
        pass

#Snippet: https://github.com/librato/python-librato/blob/master/librato/metrics.py
class LibratoExporter(BaseExporter):
    """
    Direct librato exporter module
    """
    def __init__(self, *args, **kwargs):
        super(LibratoExporter, self).__init__(*args, **kwargs)
        user = settings.URL_METRIC_LIBRATO_USER
        token = settings.URL_METRIC_LIBRATO_TOKEN
        self.connection = librato.connect(user, token)
        self.queue = self.connection.new_queue()

    def export(self, slug, value):
        self.queue.add(slug, value, type="gauge", source=self.source)

    def save(self):
        self.queue.submit()

    def metric(self, metric, value=1):
        return self.connection.submit(metric, value, source=self.source)

    def gauge(self, metric, value=1):
        return self.connection.submit(metric, value, type="gauge", source=self.source)

    def counter(self, metric, value=1):
        return self.connection.submit(metric, value, type="counter", source=self.source)

    def add_metric(self, metric_name, value = 1, logger_prefix = None):
        from url_metric.tasks import metric
        metric.delay(metric_name, value, logger_prefix)

try:
    import librato
    MAPPING["librato"] = LibratoExporter
except ImportError:
    librato = None


class DummyExporter(BaseExporter):
    instance = None

    def __new__(cls, *args, **kwargs):
        if DummyExporter.instance:
            return DummyExporter.instance

        instance = super(DummyExporter, cls).__new__(cls, *args, **kwargs)
        DummyExporter.instance = instance
        instance.metrics = {}
        return instance

    @classmethod
    def clear_metrics(cls):
        if cls.instance:
            cls.instance.metrics = {}

    def export(self, slug, value):
        self.metrics[slug] = value
        v = self.metrics.get(slug, 0)
        try:
            v += value
        except TypeError:
            v = value
        self.metrics[slug] = v

    def save(self):
        pass

    def metric(self, metric, value=1):
        self.metrics.setdefault(metric, 0)
        self.metrics[metric] += value

    def clear(self):
        self.metrics = {}

    def add_metric(self, metric_name, value = 1, logger_prefix = None):
        self.metric(metric_name, value)

MAPPING["dummy"] = DummyExporter

from django.core.cache import cache
class RedisExporter(BaseExporter):
    redis_client = cache.client.get_client()

    def __init__(self, *args, **kwargs):
        super(RedisExporter, self).__init__(*args, **kwargs)
        user = settings.URL_METRIC_LIBRATO_USER
        token = settings.URL_METRIC_LIBRATO_TOKEN
        self.connection = librato.connect(user, token)
        self.queue = self.connection.new_queue()

    def metric(self, metric, value=1, expires = None,):
        self.gauge(metric, value, expires)

    def gauge(self, metric, value=1, expires = None):
        self.add_metric_to_cache(metric, value, 'gauge', expires)

    def counter(self, metric, value=1, expires = None):
        self.add_metric_to_cache(metric, value, 'counter', expires)

    def add_metric_to_cache(self, metric, value=1, metric_type = 'gauge', expires = None):
        if not self.source:
            return

        #"¤" <- cache doesn't except this
        source_metrics = "%s_metrics" % self.source
        main_key = ":".join([self.source, metric_type, metric])

        self.redis_client.sadd(source_metrics, main_key)
        if cache.has_key(main_key):
            cache.incr(main_key, value)
        else:
            cache.add(main_key, value, expires)

        debug_logger.debug("Added to cache. source: %s %s +%s" % (self.source, main_key, value))

    def get_environment_metrics(self, source_metrics = None):
        if not source_metrics:
            source_metrics = "%s_metrics" % self.source

        results = self.redis_client.smembers(source_metrics)
        return list(results)

    def save(self, commit = True):
        if not self.source:
            return

        source_metrics = "%s_metrics" % self.source

        list_members = self.get_environment_metrics(source_metrics)
        for key in list_members:
            if cache.has_key(key):
                (source, mtype, mname) = key.split(":")
                metric_value = cache.get(key)
                self.export(mname, metric_value, mtype, source=source)
                debug_logger.debug('Added to queue. Metric name: %s, value: %s, type: %s, source: %s' % (mname, metric_value, mtype, source))

                cache.delete(key)
            self.redis_client.srem(source_metrics, key)

        if commit:
            try:
                res = self.queue.submit()
                access_logger.info(res)
            except:
                error_logger.exception('Unable to send metric')

    def clean_cache(self):
        source_metrics = "%s_metrics" % self.source
        metrics = self.get_environment_metrics(source_metrics)
        for metric in metrics:
            cache.delete(metric)
            self.redis_client.srem(source_metrics, metric)

    def export(self, slug, value, type = "gauge", source = None):
        if not source:
            source = self.source

        self.queue.add(slug, value, type=type, source=source)

    def add_metric(self, metric_name, value = 1, expires = 1800):
        try:
            self.gauge(metric_name, value, expires)

        except Exception, e:
            error_logger.exception(metric_name)


MAPPING["redis"] = RedisExporter