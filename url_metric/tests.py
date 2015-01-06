"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
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


    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_urllib2(self):
        custom_opener.urlopen("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "Google.com is not accessed 1 time. Found %s times instead" % model.count)

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       TEST_RUNNER='djcelery.contrib.test_runner.CeleryTestSuiteRunner')
    def test_urllib2(self):
        custom_opener.get("http://www.bing.com/")
        model = models.HostCounter.objects.filter(hostname="www.bing.com").first()
        self.assertIsNotNone(model, "Unable to find proper model")
        self.assertEqual(model.count, 1, "Google.com is not accessed 1 time. Found %s times instead" % model.count)
