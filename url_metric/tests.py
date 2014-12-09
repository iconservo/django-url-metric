"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.utils import override_settings
from url_metric import exports

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

