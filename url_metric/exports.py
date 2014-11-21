__author__ = 'margus'

from django.conf import settings

MAPPING = {}

try:
    import librato
except ImportError:
    librato = None
MAPPING["librato"] = librato

def get_exporter():
    ExporterClass = getattr(settings, "URL_METRIC_EXPORT_ENGINE", None)
    if not ExporterClass:
        return None

    exporter = ExporterClass()

    return exporter


class LibratoExporter(object):
    def __init__(self):
        user = settings.URL_METRIC_LIBRATO_USER
        token = settings.URL_METRIC_LIBRATO_TOKEN
        self.connection = librato.connect(user, token)
        self.queue = self.connection.new_queue()

    def export(self, slug, value, source):
        self.queue.add(slug, value, type="gauge", source=source)

    def save(self):
        self.queue.submit()