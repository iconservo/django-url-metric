"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, LiveServerTestCase
from django.test.utils import override_settings
from url_metric import exports, custom_opener, models

from django.conf import settings


class SimpleTest(TestCase):
    def test_get_exporter_none(self):
        exporter = exports.get_exporter()
        self.assertIsNone(exporter, "There should not be an url metric")


    @override_settings(URL_METRIC_EXPORT_ENGINE="librato",
                       URL_METRIC_LIBRATO_USER="test",
                        URL_METRIC_LIBRATO_TOKEN="test")
    def test_get_exporter(self):
        exporter = exports.get_exporter()
        self.assertIsNotNone(exporter, "There should be an url metric")

    @override_settings(URL_METRIC_EXPORT_ENGINE="librato",
                       URL_METRIC_LIBRATO_USER="test",
                       URL_METRIC_LIBRATO_TOKEN="test",
                       URL_METRIC_SOURCE="testing")
    def test_exporter_source(self):
        exporter = exports.get_exporter()
        self.assertIsNotNone(exporter, "There should be an url metric")
        self.assertEqual(exporter.source, "testing")

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_urllib2(self):
        custom_opener.urlopen("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "www.bing.com is not accessed 1 time. Found %s times instead" % model.count)

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_requests(self):
        custom_opener.get("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "www.bing.com is not accessed 1 time. Found %s times instead" % model.count)


class MiddlewareTest(LiveServerTestCase):
    @override_settings(URL_METRIC_URL_PATTERNS={r"200:GET:\/admin.*": "AdminPageView",
                                                r"200:PUT:\/asd/asd/.*": "Change ASD",},
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_basic_middleware(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/")
        self.assertEqual(exports.DummyExporter.instance.metrics.get("Change ASD", None), 1)

    @override_settings(URL_METRIC_URL_PATTERNS={r"200:GET:\/admin.*": "AdminPageView",
                                                r"200:PUT:\/asd/asd/.*": "Change ASD",
                                                r"200:PUT:\/asd/asd/das": "Change ASD",},
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_multiple_matches(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/das")
        self.assertEqual(exports.DummyExporter.instance.metrics.get("Change ASD", None), 1)

    @override_settings(MIDDLEWARE_CLASSES=['url_metric.middleware.RequestTimerMiddleware'],
                       URL_METRIC_EXPORT_ENGINE="dummy",)
    def test_request_timer(self):
        exports.DummyExporter.clear_metrics()
        self.client.put("/asd/asd/das")
        self.assertIsNotNone(exports.DummyExporter.instance.metrics.get("Request.Duration", None))
