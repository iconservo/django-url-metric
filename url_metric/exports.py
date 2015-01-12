__author__ = 'margus'

from django.conf import settings

MAPPING = {}

def get_exporter():
    exporter_class_name = getattr(settings, "URL_METRIC_EXPORT_ENGINE", None)
    if not exporter_class_name:
        return None

    cls = MAPPING.get(exporter_class_name, None)
    if not cls:
        return None

    exporter = cls()

    return exporter


class LibratoExporter(object):
    """
    Direct librator exporter module
    """
    def __init__(self):
        user = settings.URL_METRIC_LIBRATO_USER
        token = settings.URL_METRIC_LIBRATO_TOKEN
        self.connection = librato.connect(user, token)
        self.queue = self.connection.new_queue()

    def export(self, slug, value, source):
        self.queue.add(slug, value, type="gauge", source=source)

    def save(self):
        self.queue.submit()


try:
    import librato
    MAPPING["librato"] = LibratoExporter
except ImportError:
    librato = None


class DummyExporter(object):
    instance = None

    def __init__(self):
        DummyExporter.instance = self
        self.metrics = {}

    def export(self, slug, value, source):
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