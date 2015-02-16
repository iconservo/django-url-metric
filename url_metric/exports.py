__author__ = 'margus'

from django.conf import settings

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

class LibratoExporter(BaseExporter):
    """
    Direct librator exporter module
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

MAPPING["dummy"] = DummyExporter